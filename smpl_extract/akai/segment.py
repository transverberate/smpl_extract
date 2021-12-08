import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
from io import IOBase
from typing import List

from .data_types import AKAI_SECTOR_SIZE
from util.sector import SectorStream


class Segment(SectorStream):


    def __init__(
            self,
            partition_stream:   IOBase,
            sector_list:        List[int],
            position:           int = 0,
            buffer_length:      int = 0x1000
    ) -> None:
        super().__init__(
            partition_stream, 
            size=(AKAI_SECTOR_SIZE * len(sector_list)),
            sector_length=AKAI_SECTOR_SIZE,
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

