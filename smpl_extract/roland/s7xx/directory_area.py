from dataclasses import dataclass
from typing import cast
from typing import Dict
from construct.core import Adapter
from construct.core import Computed
from construct.core import Construct
from construct.core import FixedSized
from construct.core import PaddedString
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import Int8ul
from construct.core import Struct

from smpl_extract.util.constructs import MappingDefault
from smpl_extract.util.constructs import SafeListConstruct
from smpl_extract.util.constructs import UnsizedConstruct

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
from .data_types import RolandFileType


DirectoryEntryStruct = Struct(
    "name"              / PaddedString(16, encoding="ascii"),
    "index"             / Computed(lambda this: this._index),
    "file_type"         / MappingDefault(
        Int8ul, 
        {
            RolandFileType.VOLUME:        0x40,
            RolandFileType.PERFORMANCE:   0x41,
            RolandFileType.PATCH:         0x42,
            RolandFileType.PARTIAL:       0x43,
            RolandFileType.SAMPLE:        0x44
        },
        (RolandFileType.NONE, 0x00)
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
    name:               str
    index:              int
    file_type:          RolandFileType
    file_attributes:    int
    forward_link_ptr:   int
    backward_link_ptr:  int
    link_id:            int
    reserved:           int
    fat_entry:          int
    num_clusters:       int


class DirectoryEntryAdapter(Adapter):


    def _decode(self, obj, context, path):
        container = cast(DirectoryEntryContainer, obj)
        version = 1
        try:
            version = context["_"]["_"]["_dir_version"]
        except:
            try:
                version = context["_"]["_dir_version"]
            except:
                pass
        if version == 2:
            container.backward_link_ptr -= 0x8000
            container.forward_link_ptr -= 0x8000
        return container


    def _encode(self, obj, context, path):
        raise NotImplementedError


DirectoryEntryParser = DirectoryEntryAdapter(DirectoryEntryStruct)


def DirectoryListConstruct(num_entries: int) -> Construct:
    result = UnsizedConstruct(
        SafeListConstruct(num_entries, DirectoryEntryParser)
    )
    return result


def DirectoryAreaConstruct(
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
                DirectoryListConstruct(num_volumes)
            ),
        "performance_directories"   /\
            FixedSized(
                PERFORMANCE_DIRECTORY_AREA_SIZE,
                DirectoryListConstruct(num_performances)
            ),
        "patch_directories"         /\
            FixedSized(
                PATCH_DIRECTORY_AREA_SIZE, 
                DirectoryListConstruct(num_patches)
            ),
        "partial_directories"       /\
            FixedSized(
                PARTIAL_DIRECTORY_AREA_SIZE, 
                DirectoryListConstruct(num_partials)
            ),
        "sample_directories"        /\
            FixedSized(
                SAMPLE_DIRECTORY_AREA_SIZE, 
                DirectoryListConstruct(num_samples)
            )
    )
    return result
@dataclass
class DirectoryAreaContainer:
    volume_directories:         Dict[int, DirectoryEntryContainer]
    performance_directories:    Dict[int, DirectoryEntryContainer]
    patch_directories:          Dict[int, DirectoryEntryContainer]
    partial_directories:        Dict[int, DirectoryEntryContainer]
    sample_directories:         Dict[int, DirectoryEntryContainer]

