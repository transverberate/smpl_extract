import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from io import SEEK_CUR, SEEK_END, SEEK_SET, BufferedIOBase


class DataFileStream(BufferedIOBase):
    

    def __init__(
        self,
        partition_file: BufferedIOBase,
        offset: int,
        size: int,
        position: int = 0
    )->None:
        self.offset = offset
        self.position = position
        self.size = size
        self.partition_file = partition_file


    def _seek(self, position)->int:
        return self.partition_file.seek(self.offset + position, SEEK_SET)


    def tell(self):
        return self.position


    def seek(self, offset: int, whence: int):
        starting_position = 0
        if whence == SEEK_CUR:
            starting_position = self.position
        elif whence == SEEK_END:
            starting_position = self.size
        
        new_position = starting_position + offset
        if new_position > self.size:
            new_position = self.size
        elif new_position < 0:
            new_position = 0

        self._seek(new_position)
        self.position = new_position
        return new_position

    
    def read(self, size)->bytes:
        self._seek(self.position)
        if size < 0:
            return self.readall()
        true_size = min(self.size - self.position, size)
        if true_size < 0:
            true_size = 0
        result = self.partition_file.read(true_size)
        self.position += true_size
        return result


    def readall(self)->bytes:
        result = bytes()
        while True:
            new_read = self.read(0x1000)
            if len(new_read) < 1:
                break
            result += new_read
        
        return result

