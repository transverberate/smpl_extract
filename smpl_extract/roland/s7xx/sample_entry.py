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
from construct.core import ExprAdapter
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
from base import Printable
from .data_types import MAX_NUM_SAMPLE
from .data_types import RolandLoopMode
from .data_types import RolandSampleMode
from .data_types import SAMPLE_DIRECTORY_AREA_OFFSET
from .data_types import SAMPLE_DIRECTORY_ENTRY_SIZE
from .data_types import SAMPLE_PARAMETER_AREA_OFFSET
from .data_types import SAMPLE_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .fat import RolandFileAllocationTable
from info import InfoTable
from midi import MidiNote
from util.constructs import MappingDefault
from util.constructs import pass_expression_deeper
from util.constructs import UnsizedConstruct
from util.dataclass import get_common_field_args
from util.fat import FatNotPresent


SampleParamLoopPointStruct = Struct(
    "raw_value" / Int32ul,
    "fine"      / Computed(lambda this: (this.raw_value & 255)),
    "address"   / Computed(lambda this: (this.raw_value >> 8)),
)
@dataclass 
class SampleParamLoopPointContainer:
    raw_value:  int = 0
    fine:       int = 0
    address:    int = 0


@dataclass
class SampleParamLoopPoint:
    fine:       int = 0
    address:    int = 0


class SampleParamLoopPointAdapter(Adapter):


    def _decode(self, obj, context, path):
        del context, path  # unused
        container = cast(SampleParamLoopPointContainer, obj)
        result = SampleParamLoopPoint(
            container.fine,
            container.address
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError


SampleParamLoopPointParser = SampleParamLoopPointAdapter(
    SampleParamLoopPointStruct
)


def RolandMidiNote(subcon: Construct)->ExprAdapter:
    result = ExprAdapter(
        subcon, 
        lambda x, y: MidiNote.from_midi_byte(x),
        lambda x, y: MidiNote.to_midi_byte(x)  # type: ignore
    )
    return result


@dataclass
class SampleParamCommon:
    sustain_loop_enable:    int = 0
    sustain_loop_tune:      int = 0
    release_loop_tune:      int = 0
    original_key:           MidiNote = MidiNote.from_string("C4")
    loop_mode:              RolandLoopMode = RolandLoopMode.FORWARD_END

    start_sample: SampleParamLoopPoint = \
        field(default_factory=SampleParamLoopPoint)
    sustain_loop_start: SampleParamLoopPoint = \
        field(default_factory=SampleParamLoopPoint)
    sustain_loop_end: SampleParamLoopPoint = \
        field(default_factory=SampleParamLoopPoint)
    release_loop_start: SampleParamLoopPoint = \
        field(default_factory=SampleParamLoopPoint)
    release_loop_end: SampleParamLoopPoint = \
        field(default_factory=SampleParamLoopPoint)
    

SampleParamEntryStruct = Struct(
    "name"                  / PaddedString(16, encoding="ascii"),
    "index"                 / Computed(lambda this: this._index),
    "start_sample"          / SampleParamLoopPointParser,
    "sustain_loop_start"    / SampleParamLoopPointParser,
    "sustain_loop_end"      / SampleParamLoopPointParser,
    "release_loop_start"    / SampleParamLoopPointParser,
    "release_loop_end"      / SampleParamLoopPointParser,
    "loop_mode"             / MappingDefault(
        Int8ul,
        {
            RolandLoopMode.FORWARD_END:         0,
            RolandLoopMode.FORWARD_RELEASE:     1,
            RolandLoopMode.ONESHOT:             2,
            RolandLoopMode.FORWARD_ONESHOT:     3,
            RolandLoopMode.ALTERNATE:           4,
            RolandLoopMode.REVERSE_ONESHOT:     5,
            RolandLoopMode.REVERSE_LOOP:        6
        }, 
        (RolandLoopMode.FORWARD_END, 0)
    ),
    "sustain_loop_enable"   / Int8ul,
    "sustain_loop_tune"     / Int8ul,
    "release_loop_tune"     / Int8ul,
    "cluster_top"           / Int16ul,
    "num_clusters"          / Int16ul,
    "sample_options"        / Bitwise(Struct(
        "sample_mode"       /\
            MappingDefault(
                Nibble,
                {
                    RolandSampleMode.MONO:      0,
                    RolandSampleMode.STEREO:    1
                },
                (RolandSampleMode.MONO, 0)
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
    "original_key"          / RolandMidiNote(Int8ul),
    Padding(2)
)
@dataclass
class SampleParamOptionsSection:
    sample_mode:        RolandSampleMode    = RolandSampleMode.MONO
    sampling_frequency: int                 = 48000
@dataclass
class SampleParamEntryContainer(SampleParamCommon):
    name:                   str = ""
    index:                  int = 0

    cluster_top:            int = 0
    num_clusters:           int = 0
    sample_options: SampleParamOptionsSection = \
        field(default_factory=SampleParamOptionsSection)


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
class SampleEntry(SampleParamCommon, SampleParamOptionsSection, Element):
    directory_name: str                     = ""
    parameter_name: str                     = ""

    _data_stream:   IOBase                  = field(default_factory=IOBase)
    _parent:        Optional[Element]       = None
    _path:          List[str]               = field(default_factory=list)

    type_id:        ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:      ClassVar[str]           = "Roland S-7xx Sample"


    @property
    def name(self):
        result = self.directory_name
        return result


    def get_info(self) -> Printable:
        result = InfoTable(("",), [])
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
        
        data_stream = fat.get_file(
            container.directory.fat_entry,
            cluster_offset=container.parameter.cluster_top
        )

        common_args = get_common_field_args(
            SampleParamCommon,
            container.parameter
        )
        options_args = get_common_field_args(
            SampleParamOptionsSection,
            container.parameter.sample_options
        )

        result = SampleEntry(
            **common_args,
            **options_args,
            directory_name=container.directory.name,
            parameter_name=container.parameter.name,
            _data_stream=data_stream,
            _parent=parent,
            _path=sample_path
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError

