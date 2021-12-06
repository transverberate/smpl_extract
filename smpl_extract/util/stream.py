import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from io import IOBase
from io import SEEK_CUR
from io import SEEK_END
from io import SEEK_SET
from typing import Type
from typing import Union
from construct.core import Construct


class StreamWrapper(IOBase):
    def __init__(
            self, 
            substream: IOBase,
            size: int,
            position: int = 0,
            buffer_length: int = 0x1000
    ) -> None:
        self.substream = substream
        self.end_of_file = size 
        self.position = position 
        self.buffer_length = buffer_length


    def _translate_addr(self, address: int)->int:
        return address


    def _seek(self, address: int)->int:
        true_address = self._translate_addr(address)
        result = self.substream.seek(true_address, SEEK_SET)
        return result


    def _read(self, size: int)->bytes:
        result = self.substream.read(size)
        return result


    def tell(self)->int:
        return self.position


    def seek(self, offset: int, whence: int):
        starting_position = 0
        if whence == SEEK_CUR:
            starting_position = self.position
        elif whence == SEEK_END:
            starting_position = self.end_of_file
        
        new_position = starting_position + offset
        if new_position > self.end_of_file:
            new_position = self.end_of_file
        elif new_position < 0:
            new_position = 0

        self._seek(new_position)
        self.position = new_position
        return new_position


    def read(self, size: Union[int, None])->bytes:
        true_position = self.substream.tell()
        expected_position = self._translate_addr(self.position)
        if expected_position != true_position:
            self._seek(self.position)

        if size is None or size < 0:
            return self.readall()

        true_size = size
        if self.end_of_file is not None and self.end_of_file > 0:
            true_size = min(self.end_of_file - self.position, size)
        if true_size < 0:
            true_size = 0

        result = self._read(true_size)
        self.position += true_size
        return result


    def readall(self)->bytes:
        result = bytes()
        while True:
            new_read = self.read(self.buffer_length)
            if len(new_read) < 1:
                break
            result += new_read
        
        return result


class StreamOffset(StreamWrapper):
    

    def __init__(
            self,
            substream:      IOBase,
            size:           int,
            offset:         int,
            position:       int = 0,
            buffer_length:  int = 0x1000
    ) -> None:
        super().__init__(
            substream,
            size,
            position=position,
            buffer_length=buffer_length
        )
        self.offset = offset


    def _translate_addr(self, address: int)->int:
        true_address = self.offset + address
        return true_address


class SubStreamConstruct(Construct):

    def __init__(
            self, 
            substream_class: Type[StreamWrapper],
            *args,
            **kwargs
    ):
        super().__init__()
        self.substream_class = substream_class
        self.args = args
        self.kwargs = kwargs
        self.flagbuildnone = True


    def _eval_callable(self, x, context_inner):
            result = x(context_inner) if callable(x) else x
            return result
        
    
    def _parse(self, stream, context, path):
        del path  # Unused

        if callable(self.substream_class):
            args_eval = [self._eval_callable(arg, context) for arg in self.args]
            kwargs_eval = {key : self._eval_callable(value, context) for key, value in self.kwargs.items()}
            result = self.substream_class(stream, *args_eval, **kwargs_eval) 
        else:
            result = self.substream_class
        return result


    def _build(self, obj, stream, context, path):
        del obj  # Unused
        result = self._parse(stream, context, path)
        return result


    def _sizeof(self, context, path):
        return 0

