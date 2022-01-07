import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from io import IOBase
from io import SEEK_SET

from .stream import AttemptToReadBeyondBuffer
from .stream import SectorReadError
from .stream import StreamWrapper


class SectorStream(StreamWrapper):


    def __init__(
            self,
            parent_stream:  IOBase,
            size:           int,
            sector_length:  int,
            position:       int = 0,
            buffer_length:  int = 0x1000
    ) -> None:

        super().__init__(
            parent_stream, 
            size=size,
            position=position,
            buffer_length=buffer_length
        )

        self.sector_length = sector_length

    
    def _get_address_given_sector_index(
            self, 
            sector_index: int, 
            offset: int
        ):
        sector_address  = sector_index * self.sector_length
        
        parent_address = sector_address + offset
        return parent_address


    def _translate_address(
            self, 
            content_address: int
    )->int:

        if content_address >= self.end_of_file:
            return self.end_of_file
        
        sector_index    = content_address // self.sector_length
        sector_offset   = content_address % self.sector_length

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
        if offset + size > self.sector_length:
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

        initial_sector_index    = self.position // self.sector_length
        initial_sector_offset   = self.position % self.sector_length
        
        # read partial initial sector
        if initial_sector_offset + size <= self.sector_length:
            initial_read_size = size
        else:
            initial_read_size = self.sector_length - initial_sector_offset
        result = self._read_sector(
            initial_sector_index, 
            initial_sector_offset, 
            initial_read_size
        )
        remaining_size -= initial_read_size

        # read full size middle sectors
        i = 1
        while remaining_size > self.sector_length:
            result += self._read_sector(
                initial_sector_index + i, 
                0, 
                self.sector_length
            )
            remaining_size -= self.sector_length
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

