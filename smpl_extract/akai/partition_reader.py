import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from io import SEEK_CUR, SEEK_END, SEEK_SET, BufferedIOBase, BufferedReader
from typing import List

from .data_types import AKAI_SECTOR_SIZE


class AttemptToReadBeyondBuffer(Exception):
    pass


class SectorReadError(Exception):
    pass


def RetainOriginalState(func):
    def wrapper(self, *arg, **kwargs):
        original_position = self.image_file.tell()
        result = func(self, *arg, **kwargs)
        self.image_file.seek(original_position, SEEK_SET)
        return result
    return wrapper


class PartitionFileStream(BufferedIOBase):


    def __init__(
            self,
            image_file: BufferedIOBase,
            physical_address: int,
            sector_map: List[int],
            position: int = 0
    ) -> None:
        self.image_file = image_file 
        self.physical_address = physical_address
        self.position = position
        self.sector_map = sector_map
        self.end_of_file = AKAI_SECTOR_SIZE * len(self.sector_map)


    def _get_address_given_sector_index(
            self, 
            sector_index: int, 
            offset: int
        ):
        sector          = self.sector_map[sector_index]
        sector_address  = self.physical_address + (AKAI_SECTOR_SIZE * sector)
        
        physical_address = sector_address + offset
        return physical_address


    def _translate_address(
            self, 
            partition_address: int
    )->int:

        if partition_address >= self.end_of_file:
            return self.end_of_file
        
        sector_index    = partition_address // AKAI_SECTOR_SIZE
        sector_offset   = partition_address % AKAI_SECTOR_SIZE

        physical_address = self._get_address_given_sector_index(
            sector_index, 
            sector_offset
        )
        return physical_address


    def tell(self)->int:
        return self.position


    def _seek(self, position_abs: int):
        self.position = min(self.end_of_file, position_abs)
        return self.position
    

    def seek(self, offset: int, whence: int):
        starting_position = 0
        if whence == SEEK_CUR:
            starting_position = self.position
        elif whence == SEEK_END:
            starting_position = self.end_of_file
        
        new_position = starting_position + offset
        result = self._seek(new_position)
        return result


    def _read_sector(
            self, 
            sector_index: int, 
            offset: int, 
            size: int
    ):
        if offset + size > AKAI_SECTOR_SIZE:
            raise AttemptToReadBeyondBuffer("Reading too much")

        start_address = self._get_address_given_sector_index(
            sector_index, 
            offset
        )
    
        self.image_file.seek(start_address, SEEK_SET)
        result = self.image_file.read(size)
        # update partition position
        self.position = (sector_index * AKAI_SECTOR_SIZE) + offset + size
        return result

    
    @RetainOriginalState
    def read(self, size: int):

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
