import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from io import SEEK_CUR, SEEK_END, SEEK_SET, BufferedIOBase
from typing import Callable, Dict, List, Union
from construct import Int16ul

from .data_types import FileEntryConstruct, FILE_TABLE_END_FLAG, InvalidCharacter, VolumeType
from .sample import Sample
from .file_entry import FileEntry, InvalidFileEntry

class Volume:


    def __init__(
            self,
            sector: int,
            name: str = "",
            volume_type: VolumeType = VolumeType.INACTIVE,
            file_entries: List[FileEntry] = None
    ) -> None:
        
        self.sector = sector
        self.name = name
        self.volume_type = volume_type
        self._file_entries = file_entries or []
        self._is_files_realized = False
        self._files = {}


    def _realize_files(self):
        for file_entry in self._file_entries:
            try:
                file = file_entry.file
            except InvalidFileEntry:
                file = None

            if file is not None:
                self._files[file_entry.name] = file_entry
        self._is_files_realized = True

        
    @property
    def files(self)->Dict[str, FileEntry]:
        if not self._is_files_realized:
            self._realize_files()
        return self._files

    @property
    def children(self):
        return self.files

    @property
    def type(self):
        return self.volume_type.to_string()


    @classmethod
    def from_raw_stream(cls, 
            volume_header_stream: BufferedIOBase,
            name,
            starting_sector: int,
            volume_type: VolumeType,
            realize_file_fun: Callable[[FileEntry], None]
    )->'Volume':
        
        
        def is_table_end(stream: BufferedIOBase):
            original_address = stream.tell()

            stream.seek(8, SEEK_CUR)
            end_flag = Int16ul.parse_stream(stream)

            stream.seek(original_address, SEEK_SET)

            result = (end_flag == FILE_TABLE_END_FLAG)
            return result


        # read file entries
        volume_header_stream.seek(0, SEEK_END)
        file_table_size = volume_header_stream.tell()
        # reset to stream head
        volume_header_stream.seek(0, SEEK_SET)

        table_entry_size = FileEntryConstruct.sizeof()
        max_table_entry_cnt = file_table_size // table_entry_size

        file_entries = []
        for i in range(max_table_entry_cnt):
            if is_table_end(volume_header_stream):
                break
            file_table_entry = None
            try:
                file_table_entry = FileEntryConstruct.parse_stream(volume_header_stream)
            except InvalidCharacter:
                pass
            if file_table_entry is not None and file_table_entry.start > 0:
                filename    = file_table_entry.name
                file_type   = file_table_entry.type
                size        = file_table_entry.size
                file_sector = file_table_entry.start
                
                file_entry = FileEntry(
                    filename,
                    file_type,
                    file_sector,
                    size,
                    realize_file_fun
                )
                file_entries.append(file_entry)

        result = cls(starting_sector, name, volume_type, file_entries)

        return result
