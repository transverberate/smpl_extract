from construct.core import Adapter
from io import IOBase
from typing import List

from smpl_extract.util.fat import add_to_sector_links
from smpl_extract.util.fat import FileAllocationTable
from smpl_extract.util.fat import FileStream
from smpl_extract.util.fat import SectorLink

from .data_types import AKAI_SAT_EOF_FLAG
from .data_types import AKAI_SAT_FREE_FLAG
from .data_types import AKAI_SAT_RESERVED_FLAG_STD
from .data_types import AKAI_SAT_RESERVED_FLAG_V2
from .data_types import AKAI_SECTOR_SIZE


class Segment(FileStream):
    

    def __init__(
            self,
            partition_stream:   IOBase,
            sector_list:        List[int],
            position:           int = 0,
            buffer_length:      int = 0x1000
    ) -> None:

        super().__init__(
            partition_stream, 
            sector_size=AKAI_SECTOR_SIZE,
            sector_list=sector_list,
            position=position,
            buffer_length=buffer_length
        )


class SegmentAllocationTable(FileAllocationTable):


    def get_segment(self, index: int) -> Segment:
        sector_list = self.get_path(index)
        result = Segment(
            self.parent_stream,
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
    ) -> SegmentAllocationTable:

        del path  # Unused 
        block = obj
        if callable(self.partition_stream):
            partition_stream = self.partition_stream(context)  
        else:
            partition_stream = self.partition_stream

        size = len(block)
        sector_links = [SectorLink()] * size
        dirty_flags = [False] * size

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
                        add_to_sector_links(links, sector_links)
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
                        add_to_sector_links(links, sector_links)
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

