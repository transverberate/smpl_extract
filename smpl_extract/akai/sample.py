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
from io import  IOBase
import math
from typing import ClassVar, Container, List, Optional
from typing import Sequence
from typing import Iterable

from base import Element
from base import ElementTypes
from .akai_string import AkaiPaddedString
from .data_types import AKAI_SAMPLE_WORDLENGTH
from .data_types import DEFAULT_SAMPLE_RATE
from .data_types import AkaiLoopType
from .data_types import AkaiMidiNote
from .data_types import AkaiTuneCents
from .data_types import SampleType
from generalized.sample import ChannelConfig
from generalized.sample import Endianness
from generalized.sample import LoopRegion
from generalized.sample import Sample
from midi import MidiNote
from structural import SampleElement
from util.stream import StreamOffset
from util.stream import SubStreamConstruct
from util.constructs import EnumWrapper


@dataclass
class LoopEntry:
    loop_start:         int
    loop_end:           float
    loop_duration:      float
    repeat_forever:     bool


@dataclass
class AkaiSample(SampleElement):
    file_name:          str
    sample_name:        str
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
    _data_stream:       IOBase = field(default_factory=IOBase)
    _parent:            Optional[Element] = None
    _path:              List[str] = field(default_factory=list)

    type_id: ClassVar[ElementTypes] = ElementTypes.SampleEntry


    def __post_init__(self):
        self.type_name = str(self.sample_type)


    @property
    def name(self) -> str:
        result = self.file_name
        return result


    def to_generalized(self) -> Sample:

        loop_regions: List[LoopRegion] = []
        if self.loop_type != AkaiLoopType.LOOP_INACTIVE:
            for i, loop in enumerate(self.loop_entries):
                play_cnt = None
                if not loop.repeat_forever:
                    loop_duration = loop.loop_duration
                    loop_total_duration = (loop.loop_end - loop.loop_start) \
                        / self.sample_rate
                    if loop_total_duration == 0: 
                        continue
                    play_cnt = round(loop_duration/loop_total_duration)
                loop_regions.append(LoopRegion(
                    start_sample=loop.loop_start,
                    end_sample=math.floor(loop.loop_end),
                    repeat_forever=loop.repeat_forever,
                    play_cnt=play_cnt,
                    duration=loop.loop_duration
                ))

        data_streams = [self._data_stream]
        result = Sample(
            name=self.name,
            channel_config=ChannelConfig.MONO,
            endianness=Endianness.LITTLE,
            sample_rate=self.sample_rate,
            bytes_per_sample=self.bytes_per_sample,
            num_channels=1,
            midi_note=self.note_pitch,
            pitch_offset_semi=self.pitch_semi,
            pitch_offset_cents=self.pitch_cents,
            loop_regions=loop_regions,
            data_streams=data_streams,
            _path=self.path
        )
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
    "sample_name"           / AkaiPaddedString(12),
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
                                size=(AKAI_SAMPLE_WORDLENGTH * \
                                    (this.play_end - this.play_start)
                                ),
                                offset=(
                                    this.data_address + (AKAI_SAMPLE_WORDLENGTH * \
                                        this.play_start)
                                )
                            )
).compile()


@dataclass
class SampleHeaderContainer(Container):
    id:                 SampleType
    note_pitch:         MidiNote
    sample_name:        str 
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


    def _decode(self, obj: SampleHeaderContainer, context, path)->AkaiSample:
        del path  # Unused

        sample_header = obj
        file_name = context.get("name", sample_header.sample_name)
        if "parent" in context.keys():
            parent = context.parent
            element_path = parent.path
        else:
            parent = None
            element_path = []

        sample_path = element_path + [file_name]
        
        loop_entries = []
        if sample_header.loop_type != AkaiLoopType.LOOP_INACTIVE:
            for loop_entry in sample_header.loop_data_table:
                loop_duration = loop_entry.loop_duration
                if loop_duration > 0:
                    loop_entries.append(loop_entry)
        
        sample_rate = sample_header.sampling_rate
        if sample_rate == 0:
            sample_rate = DEFAULT_SAMPLE_RATE

        result = AkaiSample(
            file_name,
            sample_header.sample_name,
            sample_header.id,
            sample_rate,
            AKAI_SAMPLE_WORDLENGTH,
            sample_header.samples_cnt,
            sample_header.play_start,
            sample_header.play_end,
            sample_header.note_pitch,
            sample_header.pitch_offset_cents,
            sample_header.pitch_offset_semi,
            sample_header.loop_type,
            loop_entries,
            _data_stream=sample_header.data_stream,
            _parent=parent,
            _path=sample_path
        )
        return result


    def _encode(self, obj, context, path)->bytes:
        raise NotImplementedError

