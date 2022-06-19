import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from dataclasses import field
from io import IOBase
from construct.core import Adapter
from construct.core import Bitwise
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import Int8ul
from construct.core import Nibble
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Pointer
from construct.core import Struct
from typing import ClassVar
from typing import List
from typing import Optional
from typing import cast

from base import Element
from base import ElementTypes
from .data_types import LoopMode
from .data_types import MAX_NUM_SAMPLE
from .data_types import SAMPLE_DIRECTORY_AREA_OFFSET
from .data_types import SAMPLE_DIRECTORY_ENTRY_SIZE
from .data_types import SampleMode
from .data_types import SAMPLE_PARAMETER_AREA_OFFSET
from .data_types import SAMPLE_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .fat import RolandFileAllocationTable
from util.constructs import MappingDefault
from util.constructs import pass_expression_deeper
from util.constructs import UnsizedConstruct
from util.fat import FatNotPresent


SampleParamLoopPointStruct = Struct(
    "raw_value" / Int32ul,
    "fine"      / Computed(lambda this: (this.raw_value & 255)),
    "address"   / Computed(lambda this: (this.raw_value >> 8)),
)
@dataclass 
class SampleParamLoopPointContainer:
    raw_value:  int 
    fine:       int
    address:    int


SampleParamEntryStruct = Struct(
    "name"                  / PaddedString(16, encoding="ascii"),
    "index"                 / Computed(lambda this: this._index),
    "start_sample"          / SampleParamLoopPointStruct,
    "sustain_loop_start"    / SampleParamLoopPointStruct,
    "sustain_loop_end"      / SampleParamLoopPointStruct,
    "release_loop_start"    / SampleParamLoopPointStruct,
    "release_loop_end"      / SampleParamLoopPointStruct,
    "loop_mode"             / MappingDefault(
        Int8ul,
        {
            LoopMode.FORWARD_END:       0,
            LoopMode.FORWARD_RELEASE:   1,
            LoopMode.ONESHOT:           2,
            LoopMode.FORWARD_ONESHOT:   3,
            LoopMode.ALTERNATE:         4,
            LoopMode.REVERSE_ONESHOT:   5,
            LoopMode.REVERSE_LOOP:      6
        }, 
        (LoopMode.FORWARD_END, 0)
    ),
    "sustain_loop_enable"   / Int8ul,
    "sustain_loop_tune"     / Int8ul,
    "release_loop_tune"     / Int8ul,
    "seg_top"               / Int16ul,
    "seg_length"            / Int16ul,
    "sample_options"        / Bitwise(Struct(
        "sample_mode"       /\
            MappingDefault(
                Nibble,
                {
                    SampleMode.MONO:    0,
                    SampleMode.STEREO:  1
                },
                (SampleMode.MONO, 0)
            ),
        "sampling_frequency" /\
            MappingDefault(
                Nibble,
                {
                    48000: 0,
                    44100: 1,
                    24000: 2,
                    22050: 3,
                    30000: 4,
                    15000: 5
                }
            )
    )),
    "original_key"          / Int8ul,
    Padding(2)
)
@dataclass
class SampleParamOptionsSection:
    sample_mode:        SampleMode
    sampling_frequency: int
@dataclass
class SampleParamEntryContainer:
    name:                   str
    index:                  int
    start_sample:           SampleParamLoopPointContainer
    sustain_loop_start:     SampleParamLoopPointContainer
    sustain_loop_end:       SampleParamLoopPointContainer
    release_loop_start:     SampleParamLoopPointContainer
    release_loop_end:       SampleParamLoopPointContainer
    loop_mode:              LoopMode
    sustain_loop_enable:    int
    sustain_loop_tune:      int
    release_loop_tune:      int
    seg_top:                int
    seg_length:             int
    sample_options:         SampleParamOptionsSection
    original_key:           int


def SampleEntryConstruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: obj < MAX_NUM_SAMPLE
        ),
        "index"     / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (SAMPLE_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + SAMPLE_DIRECTORY_AREA_OFFSET,
            DirectoryEntryParser
        ),
        "parameter" / Pointer(
            lambda this: \
                (SAMPLE_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + SAMPLE_PARAMETER_AREA_OFFSET,
            SampleParamEntryStruct
        )
    ))
    return result
@dataclass
class SampleEntryContainer:
    index:      int
    directory:  DirectoryEntryContainer
    parameter:  SampleParamEntryContainer


@dataclass
class SampleEntry:
    index:          int
    directory_name: str
    parameter_name: str

    _data_stream:   IOBase
    _parent:        Optional[Element]       = None
    _path:          List[str]               = field(default_factory=list)

    type_id:        ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:      ClassVar[str]           = "Roland S-770 Sample"


    @property
    def name(self):
        result = self.directory_name
        return result


class SampleEntryAdapter(Adapter):


    def _decode(self, obj, context, path) -> SampleEntry:
        container = cast(SampleEntryContainer, obj)

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys():
            if "parent" in context._.keys():
                parent = cast(Element, context._.parent)
                element_path = parent.path
            if "fat" in context._.keys():
                fat = cast(RolandFileAllocationTable, context._.fat)
            else:
                raise FatNotPresent
        else:
            raise FatNotPresent

        name = container.directory.name
        sample_path = element_path + [name]
        
        data_stream = fat.get_file(container.directory.fat_entry)
        result = SampleEntry(
            container.index,
            container.directory.name,
            container.parameter.name,
            data_stream,
            parent,
            sample_path
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError

