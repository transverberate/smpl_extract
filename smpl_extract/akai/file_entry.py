import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from typing import Callable

from io import BufferedIOBase
from .sample import Sample
from .segments import RequestedInvalidSector
from .data_types import FileType, InvalidCharacter


class InvalidFileEntry(Exception):
    pass


class FileEntry:

    def  __init__(
            self,
            name: str,
            file_type: FileType,
            sector: int,
            size: int,
            realize_file_func: Callable[['FileEntry'], None]
    ) -> None:
        self.name = name 
        self.file_type = file_type
        self.sector = sector
        self.size = size
        self.realized = False
        self.invalid = False
        self.physical_address = 0
        self.get_stream: Callable[[BufferedIOBase], BufferedIOBase] = lambda x: x
        self._file = None
        self._realize_file_func = realize_file_func


    @property 
    def file(self):
        if not self.realized:
            self._realize_file_func(self)
        if self.invalid:
            raise InvalidFileEntry
        return self._file

    
    @property
    def type(self):
        return self.file_type.to_string()


    def _realize_file_callback(
        self,
        partition_segment: BufferedIOBase,
        physical_address: int,
        get_file_stream: Callable[[BufferedIOBase], BufferedIOBase],
    ):
        self.physical_address = physical_address
        self.get_stream = get_file_stream

        if self.file_type in (FileType.SAMPLE_S1000, FileType.SAMPLE_S3000):
            try:
                sample_file = Sample.from_raw_stream(partition_segment, get_file_stream)
            except (RequestedInvalidSector, InvalidCharacter):
                self.invalid = True
                return 
            self._file = sample_file
        else:
            self.invalid = True
            return
        self.realized = True
