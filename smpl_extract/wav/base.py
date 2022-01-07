import os, sys
from typing import List
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct.core import Byte
from construct.core import Const
from construct.core import Enum as EnumConstruct 
from construct.core import ExprAdapter
from construct.core import GreedyBytes
from construct.core import GreedyRange
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import Lazy
from construct.core import Prefixed
from construct.core import Rebuild
from construct.core import Struct
from construct.core import Switch
from construct.lib.containers import Container
from construct.expr import len_
from construct.expr import this
from enum import IntEnum
from dataclasses import dataclass
from dataclasses import field

from util import bytes2int
from midi import MidiNote


class SmpteFormat(IntEnum):
    NONE        = 0
    FPS24       = 24
    FPS25       = 25
    FPS30_DROP  = 29
    FPS30       = 30


class WavLoopType(IntEnum):
    FORWARD     = 0
    ALTERNATING = 1
    REVERSE     = 2
    UNKNOWN     = 3


WavLoopStruct = Struct(
    "cue_id"        / Int32ul,
    "loop_type"     / EnumConstruct(
                        Int32ul,
                        WavLoopType
                    ),
    "start_byte"    / Int32ul,
    "end_byte"      / Int32ul,
    "fraction"      / Int32ul,
    "play_cnt"      / Int32ul
)
@dataclass
class WavLoopContainer(Container):
    cue_id:     int         = bytes2int(b"loop")
    loop_type:  WavLoopType = WavLoopType.FORWARD
    start_byte: int         = 0
    end_byte:   int         = 0
    fraction:   int         = 0
    play_cnt:   int         = 0


WavSampleChunkStruct = Struct(
    "manufacturer"      / Int32ul,
    "product"           / Int32ul,
    "sample_period"     / Int32ul,
    "midi_note"         / ExprAdapter(
                            Int32ul,
                            lambda x,y: MidiNote.from_midi_byte(x),
                            lambda x,y: x.to_midi_byte()  # type: ignore
                        ),
    "pitch_fraction"    / Int32ul,
    "smpte_format"      / EnumConstruct(
                            Int32ul,
                            SmpteFormat
                        ),
    "smpte_offset"      / Int32ul,
    "sample_loop_cnt"   / Rebuild(
        Int32ul,
        len_(this.sample_loops)
    ),
    "sampler_data_size" / Rebuild(
        Int32ul,
        len_(this.sampler_data)
    ),
    "sample_loops"      / WavLoopStruct[this.sample_loop_cnt],
    "sampler_data"      / Byte[this.sampler_data_size],
)
@dataclass
class WavSampleChunkContainer(Container):
    manufacturer:       int                     = 0
    product:            int                     = 0
    sample_period:      int                     = 0
    midi_note:          MidiNote                = MidiNote.from_string("C4")
    pitch_fraction:     int                     = 0
    smpte_format:       SmpteFormat             = SmpteFormat.NONE
    smpte_offset:       int                     = 0
    sample_loops:       List[WavLoopContainer]  = field(default_factory=list)
    sampler_data:       bytes                   = b""


WavFormatChunkStruct = Struct(
    "audio_format"      / Int16ul,
    "channel_cnt"       / Int16ul,
    "sample_rate"       / Int32ul,
    "byte_rate"         / Rebuild(
        Int32ul,
        this.sample_rate * this.channel_cnt * this.bits_per_sample//8
    ),
    "block_align"       / Rebuild(
        Int16ul,
        this.channel_cnt * this.bits_per_sample//8
    ),
    "bits_per_sample"   / Int16ul
)
@dataclass 
class WavFormatChunkContainer(Container):
    audio_format:       int = 0
    channel_cnt:        int = 0
    sample_rate:        int = 0
    bits_per_sample:    int = 0


WavDataChunkStruct = Lazy(GreedyRange(GreedyBytes))


WavRiffChunkType = EnumConstruct(
    Int32ul,
    FMT=bytes2int(b"fmt "),
    SMPL=bytes2int(b"smpl"),
    DATA=bytes2int(b"data"),
)
WavRiffChunkStruct = Struct(
    "riff_id"   / WavRiffChunkType,
    "data"      / Prefixed(Int32ul, 
        Switch(this.riff_id, {
            WavRiffChunkType.FMT:  WavFormatChunkStruct,
            WavRiffChunkType.SMPL: WavSampleChunkStruct,
            WavRiffChunkType.DATA: WavDataChunkStruct
        })
    )
)


WavRiffBodyStruct = Struct(
    "fourcc"    / Const(b"WAVE"),
    "chunks"    / GreedyRange(WavRiffChunkStruct)
)


RiffStruct = Struct( 
    "fourcc"    / Const(b"RIFF"),
    "data"      / Prefixed(Int32ul, WavRiffBodyStruct),
)

