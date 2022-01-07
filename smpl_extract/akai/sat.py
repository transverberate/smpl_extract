from construct.core import Adapter
from dataclasses import dataclass
from io import IOBase
from typing import List

from .data_types import AKAI_SAT_EOF_FLAG
from .data_types import AKAI_SAT_FREE_FLAG
from .data_types import AKAI_SAT_RESERVED_FLAG_STD
from .data_types import AKAI_SAT_RESERVED_FLAG_V2
from .segment import Segment


class RequestedInvalidSector(Exception):
    pass


@dataclass
class SectorLink:
    next:   int     = 0
    end:    bool    = True


class SegmentAllocationTable:


    def __init__(
            self,
            partition_stream: IOBase,
            size: int = 0,
            sector_links: List[SectorLink] = None
    ) -> None:
        self.partition_stream = partition_stream
        self.size = size
        self.sector_links = sector_links or []

    
    def get_path(
            self, 
            starting_sector: int
    )->List[int]:

        path = []
        current_sector = starting_sector

        loop_cnt = 0
        while loop_cnt < self.size:
            if current_sector >= len(self.sector_links):
                raise RequestedInvalidSector

            path.append(current_sector)
            sector_link = self.sector_links[current_sector]

            if sector_link.end:
                break
            current_sector = sector_link.next

        if loop_cnt >= self.size:
            raise Exception("Broken FAT. Loop? Sector path exceeds size?")

        return path

    
    def get_segment(
            self,
            index: int
    )->Segment:
        sector_list = self.get_path(index)
        result = Segment(
            self.partition_stream,
            sector_list
        )
        return result
        

class SegmentAllocationTableAdapter(Adapter):


    def __init__(self, partition_stream, subcon):
        super().__init__(subcon)  # type: ignore
        self.partition_stream = partition_stream


    def _decode(
            self, 
            obj: List[int], 
            context, 
            path
    )->SegmentAllocationTable:

        del path  # Unused 
        block = obj
        if callable(self.partition_stream):
            partition_stream = self.partition_stream(context)  
        else:
            partition_stream = self.partition_stream

        size = len(block)
        sector_links = [SectorLink()] * size
        dirty_flags = [False] * size

        def add_to_sector_links(links_arg: List[int]):
            links_iter = iter(links_arg)
            prev_link = next(links_iter)
            for link in links_iter:
                sector_links[prev_link] = SectorLink(next=link, end=False)
                prev_link = link
            sector_links[prev_link] = SectorLink(next=0, end=True)

        previous_sector_was_directory = True
        for i in range(size):
            if not dirty_flags[i]:

                links = []
                subpath_index = i
                
                continue_flag = True 
                while continue_flag:
                    if subpath_index >= size:
                        continue_flag = False
                        break

                    value_current = block[subpath_index]
                    current_sector_is_directory = value_current in (
                            AKAI_SAT_RESERVED_FLAG_STD, 
                            AKAI_SAT_RESERVED_FLAG_V2
                    )

                    if not current_sector_is_directory and previous_sector_was_directory and len(links) > 0:
                        add_to_sector_links(links)
                        previous_sector_was_directory = False
                        continue_flag = False
                        break
                    elif value_current == AKAI_SAT_FREE_FLAG or \
                            (value_current < size and dirty_flags[value_current]):

                        continue_flag = False
                        dirty_flags[subpath_index] = True
                        previous_sector_was_directory = False
                        break 
                    elif value_current == AKAI_SAT_EOF_FLAG:
                        links.append(subpath_index)
                        add_to_sector_links(links)
                        dirty_flags[subpath_index] = True
                        previous_sector_was_directory = current_sector_is_directory
                        continue_flag = False
                        break
                    
                    dirty_flags[subpath_index] = True
                    links.append(subpath_index)
                    if not current_sector_is_directory:
                        subpath_index = value_current
                    else:
                        subpath_index += 1
                    previous_sector_was_directory = current_sector_is_directory
                    
            else:
                pass

        result = SegmentAllocationTable(partition_stream, size, sector_links)
        return result

    def _encode(self, obj, context, path):
        raise NotImplementedError

