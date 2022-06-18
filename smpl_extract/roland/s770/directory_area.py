import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from typing import List
from typing import cast
from construct.core import Adapter
from construct.core import Array
from construct.core import Computed
from construct.core import Construct
from construct.core import ConstructError
from construct.core import FixedSized
from construct.core import PaddedString
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import Int8ul
from construct.core import Struct

from .data_types import FileType
from .data_types import MAX_NUM_PARTIAL
from .data_types import PARTIAL_DIRECTORY_AREA_SIZE
from .data_types import MAX_NUM_PATCH
from .data_types import PATCH_DIRECTORY_AREA_SIZE
from .data_types import MAX_NUM_PERFORMANCE
from .data_types import PERFORMANCE_DIRECTORY_AREA_SIZE
from .data_types import MAX_NUM_SAMPLE
from .data_types import SAMPLE_DIRECTORY_AREA_SIZE
from .data_types import MAX_NUM_VOLUME
from .data_types import VOLUME_DIRECTORY_AREA_SIZE
from util.constructs import MappingDefault


DirectoryEntryStruct = Struct(
    "name"              / PaddedString(16, encoding="ascii"),
    "index"             / Computed(lambda this: this._index),
    "file_type"         / MappingDefault(
        Int8ul, 
        {
            FileType.VOLUME:        0x40,
            FileType.PERFORMANCE:   0x41,
            FileType.PATCH:         0x42,
            FileType.PARTIAL:       0x43,
            FileType.SAMPLE:        0x44
        },
        (FileType.NONE, 0x00)
    ),
    "file_attributes"   / Int8ul,
    "forward_link_ptr"  / Int16ul,
    "backward_link_ptr" / Int16ul,
    "link_id"           / Int16ul,
    "reserved"          / Int32ul,
    "fat_entry"         / Int16ul,
    "num_clusters"      / Int16ul
)
@dataclass
class DirectoryEntryContainer:
    name_raw:           bytes
    name:               str
    index:              int
    file_type:          FileType
    file_attributes:    int
    forward_link_ptr:   int
    backward_link_ptr:  int
    link_id:            int
    reserved:           int
    fat_entry:          int
    num_clusters:       int


def DirectoryListStruct(num_entries: int) -> Construct:
    result = Array(num_entries, DirectoryEntryStruct)
    return result


class DirectoryListAdapter(Adapter):


    def _fix_directory_entry(self, entry: DirectoryEntryContainer):
        entry.forward_link_ptr  -= 0x8000
        entry.backward_link_ptr -= 0x8000


    def _decode(self, obj, context, path) -> List[DirectoryEntryContainer]:
        del path  # unused

        fat_version = 1
        if "_" in context.keys() and "fat_version" in context._.keys():
            fat_version = context._.fat_version

        if fat_version not in (1, 2):
            raise ConstructError(f"Unknown FAT version {fat_version}")
        
        fix_entry_f = lambda x: x  # do nothing
        if fat_version == 2:
            fix_entry_f = self._fix_directory_entry

        directories = cast(List[DirectoryEntryContainer], obj)
        filtered_directories = []
        for directory_entry in directories:
            try:
                directory_entry.name = directory_entry.name_raw.decode("ascii")
            except UnicodeDecodeError:
                continue
            disqualifiers = (
                len(directory_entry.name) <= 0,
                directory_entry.file_type == FileType.NONE
            )
            if any(disqualifiers):
                continue
            
            fix_entry_f(directory_entry)
            filtered_directories.append(directory_entry)

        return filtered_directories


    def _encode(self, obj, context, path):
        raise NotImplementedError


def DirectoryAreaStruct(
    num_volumes:        int = MAX_NUM_VOLUME,
    num_performances:   int = MAX_NUM_PERFORMANCE,
    num_patches:        int = MAX_NUM_PATCH,
    num_partials:       int = MAX_NUM_PARTIAL,
    num_samples:        int = MAX_NUM_SAMPLE
) -> Construct:
    result = Struct(
        "volume_directories"        /\
            FixedSized(
                VOLUME_DIRECTORY_AREA_SIZE, 
                DirectoryListAdapter(
                    DirectoryListStruct(num_volumes)
                )
            ),
        "performance_directories"   /\
            FixedSized(
                PERFORMANCE_DIRECTORY_AREA_SIZE,
                DirectoryListAdapter(
                    DirectoryListStruct(num_performances)
                )
            ),
        "patch_directories"         /\
            FixedSized(
                PATCH_DIRECTORY_AREA_SIZE, 
                DirectoryListAdapter(
                    DirectoryListStruct(num_patches)
                )
            ),
        "partial_directories"       /\
            FixedSized(
                PARTIAL_DIRECTORY_AREA_SIZE, 
                DirectoryListAdapter(
                    DirectoryListStruct(num_partials)
                )
            ),
        "sample_directories"        /\
            FixedSized(
                SAMPLE_DIRECTORY_AREA_SIZE, 
                DirectoryListAdapter(
                    DirectoryListStruct(num_samples)
                )
            )
    )
    return result
@dataclass
class DirectoryAreaContainer:
    volume_directories:         List[DirectoryEntryContainer]
    performance_directories:    List[DirectoryEntryContainer]
    patch_directories:          List[DirectoryEntryContainer]
    partial_directories:        List[DirectoryEntryContainer]
    sample_directories:         List[DirectoryEntryContainer]

