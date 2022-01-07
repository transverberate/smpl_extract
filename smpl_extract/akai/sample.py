import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct.core import Adapter
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import Int8sl
from construct.core import Int8ul
from construct.core import Padding
from construct.core import Struct
from construct.core import Tell
from construct.expr import this
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from io import  IOBase
from typing import Container
from typing import Sequence
from typing import Iterable

from .akai_string import AkaiPaddedString
from .data_types import AKAI_SAMPLE_WORDLENGTH
from .data_types import AkaiLoopType
from .data_types import AkaiMidiNote
from .data_types import AkaiTuneCents
from .data_types import SampleType
from midi import MidiNote
from util.stream import StreamOffset
from util.stream import SubStreamConstruct
from util.constructs import EnumWrapper
from util.dataclass import itemizable
import util.dataclass


@itemizable
@dataclass
class LoopEntry:
    loop_start: int
    loop_end: float
    loop_duration: float
    repeat_forever: bool


@dataclass
class Sample:
    name: str
    sample_type:        SampleType
    sample_rate:        int
    bytes_per_sample:   int
    samples_cnt:        int
    start_sample:       int
    end_sample:         int
    note_pitch:         MidiNote = MidiNote.from_string("C4")
    pitch_cents:        int = 0
    pitch_semi:         int = 0
    loop_type:          AkaiLoopType = AkaiLoopType.LOOP_INACTIVE
    loop_entries:       Sequence[LoopEntry] = tuple()
    data_stream:        IOBase = field(default_factory=IOBase)


    def itemize(self):
        items = {
            k.name: getattr(self, k.name) 
            for k in fields(self) if k.name != "data_stream"
        }
        result = util.dataclass.itemize(items)
        return result
      

LoopDataConstruct = Struct(
    "loop_start" / Int32ul,
    "loop_length_fine" / Int16ul,
    "loop_length_coarse" / Int32ul,
    "loop_duration" / Int16ul
).compile()
@dataclass
class LoopDataContainer(Container):
    loop_start:         int 
    loop_length_fine:   int 
    loop_length_coarse: int 
    loop_duration:      int


class LoopEntryAdapter(Adapter):
    def _decode(self, obj: LoopDataContainer, context, path)->LoopEntry:
        del context, path  # Unused

        loop_data = obj
        
        loop_at = loop_data.loop_start
        loop_length = loop_data.loop_length_coarse
        
        loop_duration = loop_data.loop_duration
        repeat_forever = (loop_duration >= 9999)

        loop_start = (loop_at - 1) - loop_length
        if loop_start < 0:
            loop_start = 0
        loop_end = loop_at

        result = LoopEntry(
            loop_start,
            loop_end, 
            loop_duration, 
            repeat_forever
        )
        return result


    def _encode(self, obj, context, path)->bytes:
        raise NotImplementedError


SampleHeaderConstruct = Struct(
    "id"                    / EnumWrapper(Int8ul, SampleType),
    Padding(1),
    "note_pitch"            / AkaiMidiNote(Int8ul),
    "name"                  / AkaiPaddedString(12),
    Padding(4),
    "loop_type"             / EnumWrapper(Int8ul, AkaiLoopType),
    "pitch_offset_cents"    / AkaiTuneCents(Int8sl),
    "pitch_offset_semi"     / Int8sl,
    Padding(4),
    "samples_cnt"           / Int32ul,
    "play_start"            / Int32ul,
    "play_end"              / Int32ul,
    "loop_data_table"       / LoopEntryAdapter(LoopDataConstruct)[8],
    Padding(4),
    "sampling_rate"         / Int16ul,
    "data_address"          / Tell,
    "data_stream"           / SubStreamConstruct(
                                StreamOffset, 
                                size=(AKAI_SAMPLE_WORDLENGTH * this.samples_cnt),
                                offset=this.data_address
                            )
).compile()


@dataclass
class SampleHeaderContainer(Container):
    id:                 SampleType
    note_pitch:         MidiNote
    name:               str 
    loop_type:          AkaiLoopType
    pitch_offset_cents: int
    pitch_offset_semi:  int
    samples_cnt:        int 
    play_start:         int 
    play_end:           int
    loop_data_table:    Iterable[LoopEntry]
    sampling_rate:      int
    data_stream:        IOBase


class SampleAdapter(Adapter):


    def _decode(self, obj: SampleHeaderContainer, context, path)->Sample:
        del context, path  # Unused

        sample_header = obj
        
        loop_entries = []
        if sample_header.loop_type != AkaiLoopType.LOOP_INACTIVE:
            for loop_entry in sample_header.loop_data_table:
                loop_duration = loop_entry.loop_duration
                if loop_duration > 0:
                    loop_entries.append(loop_entry)

        result = Sample(
            sample_header.name,
            sample_header.id,
            sample_header.sampling_rate,
            AKAI_SAMPLE_WORDLENGTH,
            sample_header.samples_cnt,
            sample_header.play_start,
            sample_header.play_end,
            sample_header.note_pitch,
            sample_header.pitch_offset_cents,
            sample_header.pitch_offset_semi,
            sample_header.loop_type,
            loop_entries,
            sample_header.data_stream
        )
        return result


    def _encode(self, obj, context, path)->bytes:
        raise NotImplementedError

