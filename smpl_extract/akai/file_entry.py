import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from construct.core import Computed
from construct.core import ConstructError
from construct.core import Lazy
from construct.core import Struct
from construct.core import Padding
from construct.core import Int8ul
from construct.core import Int16ul
from construct.core import Int24ul
from construct.core import StreamError
from construct.core import Subconstruct
from construct.lib.containers import Container
from construct.expr import this
from dataclasses import dataclass
from io import SEEK_CUR
from io import SEEK_END
from io import SEEK_SET
from typing import Callable, Optional, cast
from typing import Iterable
from typing import List
from typing import Union

from .akai_string import AkaiPaddedString
from base import Element
from .data_types import FILE_TABLE_END_FLAG
from .data_types import FileType
from .file import FileAdapter
from .file import FileConstruct
from .sat import RequestedInvalidSector
from util.stream import StreamWrapper
from util.constructs import EnumWrapper


class InvalidFileEntry(Exception):
    pass


class FileEntry:

    def  __init__(
            self,
            name: str,
            file_type: FileType,
            f_file_content: Callable
    ) -> None:
        self.name = name 
        self.file_type = file_type
        self._file = None 
        self._f_file_content = f_file_content


    @property 
    def file(self):
        if not self._file:
            self._file = self._f_file_content()
        return self._file


FileEntryConstruct = Struct(
    "name"      / AkaiPaddedString(12),
    Padding(4),
    "file_type" / EnumWrapper(Int8ul, FileType),  
    "size"      / Int24ul,
    "start"     / Int16ul,
    Padding(2),
    "file_stream" / Computed(lambda this:
        StreamWrapper(this._.sat.get_segment(this.start), this.size)
    )
)
@dataclass
class FileEntryContainer(Container):
    name:           str
    file_type:      FileType
    size:           int
    start:          int
    file_stream:    StreamWrapper


class FileEntriesAdapter(Subconstruct):


    def __init__(self, sat, subcon):
        super().__init__(subcon)  # type: ignore
        self.sat = sat


    def _parse(self, stream, context, path)->Iterable[FileEntry]:


        def is_table_end(stream_inner):
            original_address = stream_inner.tell()

            stream_inner.seek(8, SEEK_CUR)
            try:
                end_flag = Int16ul.parse_stream(stream_inner)
            except (StreamError):
                return True

            stream_inner.seek(original_address, SEEK_SET)

            result = (end_flag == FILE_TABLE_END_FLAG)
            return result

        sat = self.sat(context) if callable(self.sat) else self.sat
        parent: Optional[Element] = None
        if "_" in context.keys() and "parent" in context._.keys():
            parent = cast(Element, context._.parent)

        # read file entries containers
        stream.seek(0, SEEK_END)
        file_table_size = stream.tell()
        stream.seek(0, SEEK_SET)

        table_entry_size = self.subcon.sizeof()
        max_table_entry_cnt = file_table_size // table_entry_size
        
        file_entries: List[FileEntry] = []
        for _i in range(max_table_entry_cnt):
            if is_table_end(stream):
                break
            file_entry_container: Union[FileEntryContainer, None] = None
            try:
                file_entry_container = self.subcon.parse_stream(stream, _=context, sat=sat)
            except (ConstructError, RequestedInvalidSector):
                pass

            if file_entry_container is not None and file_entry_container.start > 0:
                name = file_entry_container.name
                file_content = Lazy(FileAdapter(
                        this._.sat,
                        FileConstruct
                    )).parse_stream(
                        file_entry_container.file_stream,  # type: ignore
                        _=context,
                        type=file_entry_container.file_type,
                        name=name,
                        parent=parent
                    )

                if file_content is None:
                    raise ConstructError

                file_entry = FileEntry(
                    file_entry_container.name,
                    file_entry_container.file_type,
                    file_content
                )

                file_entries.append(file_entry)

        result = file_entries
        return result


    def _build(self, obj, stream, context, path):
        raise NotImplementedError

