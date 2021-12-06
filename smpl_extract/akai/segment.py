import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
from io import IOBase
from io import SEEK_SET
from typing import List

from .data_types import AKAI_SECTOR_SIZE
from util.stream import StreamWrapper


class AttemptToReadBeyondBuffer(Exception):
    pass


class SectorReadError(Exception):
    pass


class Segment(StreamWrapper):


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
            position=position,
            buffer_length=buffer_length
        )
        self.sector_list = sector_list

    
    def _get_address_given_sector_index(
            self, 
            sector_index: int, 
            offset: int
        ):
        sector          = self.sector_list[sector_index]
        sector_address  = AKAI_SECTOR_SIZE * sector
        
        partition_address = sector_address + offset
        return partition_address


    def _translate_address(
            self, 
            segment_address: int
    )->int:

        if segment_address >= self.end_of_file:
            return self.end_of_file
        
        sector_index    = segment_address // AKAI_SECTOR_SIZE
        sector_offset   = segment_address % AKAI_SECTOR_SIZE

        partition_address = self._get_address_given_sector_index(
            sector_index, 
            sector_offset
        )
        return partition_address


    def _read_sector(
            self, 
            sector_index: int, 
            offset: int, 
            size: int
    )->bytes:
        if offset + size > AKAI_SECTOR_SIZE:
            raise AttemptToReadBeyondBuffer("Reading too much")

        start_address = self._get_address_given_sector_index(
            sector_index, 
            offset
        )
    
        self.substream.seek(start_address, SEEK_SET)
        result = self.substream.read(size)
        return result

    
    def _read(self, size: int)->bytes:

        remaining_size = size

        initial_sector_index    = self.position // AKAI_SECTOR_SIZE
        initial_sector_offset   = self.position % AKAI_SECTOR_SIZE
        
        # read partial initial sector
        if initial_sector_offset + size <= AKAI_SECTOR_SIZE:
            initial_read_size = size
        else:
            initial_read_size = AKAI_SECTOR_SIZE - initial_sector_offset
        result = self._read_sector(
            initial_sector_index, 
            initial_sector_offset, 
            initial_read_size
        )
        remaining_size -= initial_read_size

        # read full size middle sectors
        i = 1
        while remaining_size > AKAI_SECTOR_SIZE:
            result += self._read_sector(
                initial_sector_index + i, 
                0, 
                AKAI_SECTOR_SIZE
            )
            remaining_size -= AKAI_SECTOR_SIZE
            i += 1
        
        # read partial final sector
        final_sector_index = initial_sector_index + i
        if remaining_size > 0:
            result += self._read_sector(
                final_sector_index, 
                0, 
                remaining_size
            )

        if len(result) != size:
            raise SectorReadError(f"Wanted {size}, read {len(result)}.")

        return result

