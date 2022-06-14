import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from dataclasses import dataclass
from io import IOBase
from typing import List
from typing import Optional

from util.sector import SectorStream


class RequestedInvalidSector(Exception): ...
class InvalidFatDefinition(Exception): ...


class FileStream(SectorStream):


    def __init__(
            self,
            parent_stream:      IOBase,
            sector_size:        int,
            sector_list:        List[int],
            position:           int = 0,
            buffer_length:      int = 0x1000
    ) -> None:
        super().__init__(
            parent_stream, 
            size=(sector_size * len(sector_list)),
            sector_length=sector_size,
            position=position,
            buffer_length=buffer_length
        )
        self.sector_list = sector_list

    
    def _get_address_given_sector_index(
            self, 
            sector_index: int, 
            offset: int
        ):
        sector  = self.sector_list[sector_index]
        result  = super()._get_address_given_sector_index(
            sector,
            offset
        )
        return result


@dataclass
class SectorLink:
    next:   int     = 0
    end:    bool    = True


def add_to_sector_links(
        links_arg:      List[int], 
        sector_links:   List[SectorLink]
    ):

    links_iter = iter(links_arg)
    prev_link = next(links_iter)
    try:
        for link in links_iter:
            sector_links[prev_link] = SectorLink(next=link, end=False)
            prev_link = link
        sector_links[prev_link] = SectorLink(next=0, end=True)

    except IndexError as e:
        raise InvalidFatDefinition(
            f"FAT entry {prev_link} exceeds total "
            f"number of FAT entries {len(sector_links)}."
        ) from e


class FileAllocationTable:


    def __init__(
            self,
            parent_stream: IOBase,
            size: int = 0,
            sector_links: Optional[List[SectorLink]] = None
    ) -> None:
        self.parent_stream = parent_stream
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
            raise InvalidFatDefinition("Broken FAT. Loop? Sector path exceeds size?")

        return path

