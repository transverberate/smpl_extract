import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct.core import Adapter
from construct.core import Computed
from construct.core import Default
from construct.core import ExprSymmetricAdapter
from construct.core import FocusedSeq
from construct.core import If
from construct.core import Int16ul
from construct.core import Int8sl
from construct.core import Int8ul
from construct.core import Padding
from construct.core import Seek
from construct.core import Struct
from construct.expr import this
from construct.lib.containers import Container
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from typing import Sequence

from .akai_string import AkaiPaddedString
from base import Element
from .data_types import AkaiAuxOutput
from .data_types import AkaiMidiNote
from .data_types import AkaiMidiOutput
from .data_types import AkaiTuneCents
from .data_types import AkaiVoiceReassign
from .data_types import AkaiProgramPriority
from elements import ProgramElement
from .keygroup import Keygroup
from .keygroup import KeygroupAdapter
from .keygroup import KeygroupConstruct
from midi import MidiNote
from util.constructs import BoolConstruct
from util.constructs import EnumWrapper
from util.constructs import MappingDefault
from util.dataclass import get_common_field_args


@dataclass
class ProgramHeaderCommon:
    program_id:             int = 1
    program_name:           str = "" 
    midi_program_number:    int = 0
    midi_channel:           AkaiMidiOutput = AkaiMidiOutput(0)
    polyphony:              int = 15
    priority:               AkaiProgramPriority = AkaiProgramPriority.NORMAL 
    low_key:                MidiNote = MidiNote.from_string("C0")
    high_key:               MidiNote = MidiNote.from_string("G8") 
    octave_shift:           int = 0
    aux_output_select:      AkaiAuxOutput = AkaiAuxOutput.OFF
    mix_output_level:       int = 99
    mix_output_pan:         int = 0
    volume:                 int = 80
    vel_to_volume:          int = 20
    key_to_volume:          int = 0
    pres_to_volume:         int = 0
    pan_lfo_rate:           int = 50
    pan_lfo_depth:          int = 0
    pan_lfo_delay:          int = 0
    key_to_pan:             int = 0
    lfo_rate:               int = 50
    lfo_depth:              int = 0
    lfo_delay:              int = 0
    mod_to_lfo_depth:       int = 30
    pres_to_lfo_depth:      int = 0
    vel_to_lfo_depth:       int = 0
    bend_to_pitch:          int = 2
    pres_to_pitch:          int = 0
    keygroup_crossfade:     bool = False
    number_of_keygroups:    int = 1
    key_temperaments:       Sequence[int] = field(default=(0,)*12)
    fx_output:              bool = False
    mod_to_pan:             int = 0
    stereo_coherence:       bool = False
    lfo_desync:             bool = True
    pitch_law:              int = 0
    voice_reassign:         AkaiVoiceReassign = AkaiVoiceReassign.OLDEST
    softped_to_volume:      int = 10
    softped_to_attack:      int = 10
    softped_to_filter:      int = 10
    tune_cents:             int = 0
    tune_semitones:         int = 0
    key_to_lfo_rate:        int = 0
    key_to_lfo_depth:       int = 0
    key_to_lfo_delay:       int = 0
    voice_output_scale_db:  float = 1.0
    stereo_output_scale_db: float = 0.0


@dataclass
class ProgramHeaderContainer(ProgramHeaderCommon, Container):
    first_keygroup_address: int = 150        


    def get_info(self):
        items = {key: str(value) for key, value in self.items() if key != "_io"}
        result = dict(items)
        return result


ProgramHeaderConstruct = Struct(
    "program_id"                /\
        Int8ul,
    "first_keygroup_address"    /\
        Default(Int16ul, 150),
    "program_name"              /\
        AkaiPaddedString(12),
    "midi_program_number"       /\
        Int8ul,
    "midi_channel"              /\
        ExprSymmetricAdapter(
            Int8ul,
            lambda x,y: 
            AkaiMidiOutput(x)   # type: ignore
        ),
    "polyphony"                 /\
        Int8ul,
    "priority"                  /\
        EnumWrapper(
            Int8ul, 
            AkaiProgramPriority 
        ),
    "low_key"                   /\
        AkaiMidiNote(Int8ul),
    "high_key"                  /\
        AkaiMidiNote(Int8ul),
    "octave_shift"              /\
        Int8sl,
    "aux_output_select"         /\
        ExprSymmetricAdapter(
            Int8ul,
            lambda x,y: 
            AkaiAuxOutput(x)    # type: ignore
        ),
    "mix_output_level"          /\
        Int8ul,
    "mix_output_pan"            /\
        Int8sl,
    "volume"                    /\
        Int8ul,
    "vel_to_volume"             /\
        Int8sl,
    "key_to_volume"             /\
        Int8sl,
    "pres_to_volume"            /\
        Int8sl,
    "pan_lfo_rate"              /\
        Int8ul,
    "pan_lfo_depth"             /\
        Int8ul,
    "pan_lfo_delay"             /\
        Int8ul,
    "key_to_pan"                /\
        Int8sl,
    "lfo_rate"                  /\
        Int8ul,
    "lfo_depth"                 /\
        Int8ul,
    "lfo_delay"                 /\
        Int8ul,
    "mod_to_lfo_depth"          /\
        Int8ul,
    "pres_to_lfo_depth"         /\
        Int8ul,
    "vel_to_lfo_depth"          /\
        Int8ul,
    "bend_to_pitch"             /\
        Int8ul,
    "pres_to_pitch"             /\
        Int8sl,
    "keygroup_crossfade"        /\
        BoolConstruct(Int8ul),
    "number_of_keygroups"       /\
        Int8ul,
    Padding(1),                 # program number
    "key_temperaments"          /\
        Int8ul[12],
    "fx_output"                 /\
        BoolConstruct(Int8ul),
    "mod_to_pan"                /\
        Int8sl,
    "stereo_coherence"          /\
        BoolConstruct(Int8ul),
    "lfo_desync"                /\
        BoolConstruct(Int8ul), 
    "pitch_law"                 /\
        Int8ul,
    "voice_reassign"            /\
        EnumWrapper(
            Int8ul,
            AkaiVoiceReassign
        ),
    "softped_to_volume"         /\
        Int8ul,
    "softped_to_attack"         /\
        Int8ul,
    "softped_to_filter"         /\
        Int8ul,
    "tune_cents"                /\
        AkaiTuneCents(Int8sl),
    "tune_semitones"            /\
        Int8sl,
    "key_to_lfo_rate"           /\
        Int8sl,
    "key_to_lfo_depth"          /\
        Int8sl,
    "key_to_lfo_delay"          /\
        Int8sl,
    "voice_output_scale_db"     /\
        MappingDefault(Int8ul,
            {
                -6: 0,
                0:  1,
                12: 2
            },
            (0, 1) 
        ),
    "stereo_output_scale_db"    /\
        MappingDefault(Int8ul, 
        {
            0: 0,
            6: 1
        },
        (0, 0) 
    )
)


def _has_next_keygroup(this)->bool:
    result = this.keygroup_raw.next_keygroup_address > 0 \
                and this._index < this._.header.number_of_keygroups - 1
    return result


KeygroupLinkConstruct = FocusedSeq(
    "keygroup",
    "keygroup_raw"  / KeygroupConstruct,
    "keygroup"      / KeygroupAdapter(Computed(this.keygroup_raw)),
    If(_has_next_keygroup,
        Seek(this.keygroup_raw.next_keygroup_address)
    )
)


def _has_valid_first_keygroup(this)->bool:
    result = (this.header.first_keygroup_address > 0 
        and this.header.number_of_keygroups > 0)
    return result


@dataclass
class ProgramContainer:
    header:     ProgramHeaderContainer  = field(default_factory=ProgramHeaderContainer)
    keygroups:  Sequence[Keygroup]      = field(default_factory=Sequence[Keygroup])


@dataclass
class Program(ProgramHeaderCommon, ProgramElement):
    keygroups:  Sequence[Keygroup]      = field(default_factory=Sequence[Keygroup])
    file_name:  str                     = ""
    type_name:  str                     = ""
    _parent:    Optional[Element]       = None
    _path:      List[str]               = field(default_factory=list)

    @property
    def name(self) -> str:
        result = self.file_name
        return result


class ProgramAdapter(Adapter):

    def _encode(self, obj, context, path):
        raise NotImplementedError

    def _decode(self, obj: ProgramContainer, context, path)->Program:
        del path  # Unused
        header_args = get_common_field_args(ProgramHeaderCommon, obj.header)

        file_name = context.get("name", obj.header.program_name)
        type_name = str(context.get("type", "AKAI Program"))
        if "parent" in context.keys():
            parent = context.parent
            element_path = parent.path
        else:
            parent = None
            element_path = []
            
        program_path = element_path + [file_name]

        result = Program(
            **header_args, 
            keygroups=obj.keygroups, 
            file_name=file_name,
            type_name=type_name,
            _parent=parent,
            _path=program_path
        )
        return result


ProgramParser = ProgramAdapter(Struct(
    "header" / ProgramHeaderConstruct,
    If(_has_valid_first_keygroup,
        Seek(this.header.first_keygroup_address)
    ),
    "keygroups" / KeygroupLinkConstruct[this.header.number_of_keygroups]
))

