from midi import MidiNote
from construct_assist import ConstructAssist
from enum import IntEnum
from typing import List

from construct import this
from construct.core import Byte, Const, Int32ul, Struct, ExprAdapter, Int16ul


class SmpteFormat(IntEnum):
    NONE        = 0
    FPS24       = 24
    FPS25       = 25
    FPS30_DROP  = 29
    FPS30       = 30
    @classmethod
    def from_int(cls, int_in: int):
        if int_in not in [e.value for e in cls]:
            return cls.NONE
        return SmpteFormat(int_in)
    def to_int(self):
        return int(self)


class WavLoopType(IntEnum):
    FORWARD     = 0
    ALTERNATING = 1
    REVERSE     = 2
    UNKOWN      = 3
    @classmethod
    def from_int(cls, int_in: int):
        if int_in not in [e.value for e in cls]:
            return cls.UNKOWN
        return SmpteFormat(int_in)
    def to_int(self):
        return int(self)


WavLoopConstructGen = Struct(
    "cue_id"        / Int32ul,
    "loop_type"     / ExprAdapter(
                        Int32ul,
                        lambda x,y: WavLoopType.from_int(x),
                        lambda x,y: WavLoopType.to_int(x)
                    ),
    "start_byte"    / Int32ul,
    "end_byte"      / Int32ul,
    "fraction"      / Int32ul,
    "play_cnt"      / Int32ul
)
WavLoopConstruct = WavLoopConstructGen.compile()


class WavLoopStruct(ConstructAssist):
    def __init__(
            self,
            cue_id:     int         = None,
            loop_type:  WavLoopType = WavLoopType.FORWARD,
            start_byte: int         = 0,
            end_byte:   int         = 0,
            fraction:   int         = 0,
            play_cnt:   int         = 0
    ):
        super().__init__(WavLoopConstruct)
        self.cue_id = cue_id or int.from_bytes(b"loop", "little")
        self.loop_type = loop_type
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.fraction = fraction
        self.play_cnt = play_cnt

    
    def get_dict(self)->dict:
        return dict(
            cue_id      = self.cue_id,
            loop_type   = self.loop_type,
            start_byte  = self.start_byte,
            end_byte    = self.end_byte,
            fraction    = self.fraction,
            play_cnt    = self.play_cnt
        )


WavSampleChunkConstructGen = Struct(
    "chunk_id"          / Const(b"smpl"),
    "size"              / Int32ul,
    "manufacturer"      / Int32ul,
    "product"           / Int32ul,
    "sample_period"     / Int32ul,
    "midi_note"         / ExprAdapter(
                            Int32ul,
                            lambda x,y: MidiNote.from_midi_byte(x),
                            lambda x,y: x.to_midi_byte()
                        ),
    "pitch_fraction"    / Int32ul,
    "smpte_format"      / ExprAdapter(
                            Int32ul,
                            lambda x,y: SmpteFormat.from_int(x),
                            lambda x,y: x.to_int()
                        ),
    "smpte_offset"      / Int32ul,
    "sample_loop_cnt"   / Int32ul,
    "sampler_data_size" / Int32ul,
    "sample_loops"      / WavLoopConstructGen[this.sample_loop_cnt],
    "sampler_data"      / Byte[this.sampler_data_size],
)
WavSampleChunkConstruct = WavSampleChunkConstructGen.compile()


class WavSampleChunkStruct(ConstructAssist):
    def __init__(
            self,
            manufacturer:       int                     = 0,
            product:            int                     = 0,
            sample_period:      int                     = 0,
            midi_note:          MidiNote                = None,
            pitch_fraction:     int                     = 0,
            smpte_format:       SmpteFormat             = SmpteFormat.NONE,
            smpte_offset:       int                     = 0,
            sample_loops:       List[WavLoopStruct]     = None,
            sampler_data:       bytes                   = b"",
    ):
        super().__init__(WavSampleChunkConstruct)
        self.manufacturer   = manufacturer
        self.product        = product
        self.sample_period  = sample_period
        self.midi_note      = midi_note or MidiNote(MidiNote.ScaleDegree.C, False, 4)
        self.pitch_fraction = pitch_fraction
        self.smpte_format   = smpte_format
        self.smpte_offset   = smpte_offset
        self.sample_loops   = sample_loops or []
        self.sampler_data   = sampler_data


    @property
    def sampler_data_size(self):
        sampler_data_size = len(self.sampler_data)
        return sampler_data_size


    @property
    def sample_loop_cnt(self):
        sample_loop_cnt = len(self.sample_loops)
        return sample_loop_cnt

   
    @property
    def size(self):
        size = 36 + (self.sample_loop_cnt * 24) + self.sampler_data_size
        return size
        

    def get_dict(self):
        sample_loop_dicts = list(map(lambda x: x.get_dict(), self.sample_loops))
        return dict(
            size=self.size,
            manufacturer=self.manufacturer,
            product=self.product,
            sample_period=self.sample_period,
            midi_note=self.midi_note,
            pitch_fraction=self.pitch_fraction,
            smpte_format=self.smpte_format,
            smpte_offset=self.smpte_offset,
            sample_loop_cnt=self.sample_loop_cnt,
            sampler_data_size=self.sampler_data_size,
            sample_loops=sample_loop_dicts,
            sampler_data=self.sampler_data
        )


WavFormatChunkConstructGen = Struct(
    "chunk_id"          / Const(b"fmt "),
    "size"              / Int32ul,
    "audio_format"      / Int16ul,
    "channel_cnt"       / Int16ul,
    "sample_rate"       / Int32ul,
    "byte_rate"         / Int32ul,
    "block_align"       / Int16ul,
    "bits_per_smaple"   / Int16ul
)
WavFormatChunkConstruct = WavFormatChunkConstructGen.compile()


class WavFormatChunkStruct(ConstructAssist):
    def __init__(
            self,
            audio_format:       int = 0,
            channel_cnt:        int = 0,
            sample_rate:        int = 0,
            bits_per_smaple:    int = 0
    ):
        super().__init__(WavFormatChunkConstruct)
        self.audio_format = audio_format
        self.channel_cnt = channel_cnt
        self.sample_rate = sample_rate
        self.bits_per_smaple = bits_per_smaple


    @property
    def size(self):
        return 16

    
    @property
    def byte_rate(self):
        byte_rate = int(self.sample_rate * self.channel_cnt * self.bits_per_smaple//8)
        return byte_rate
    

    @property
    def block_align(self):
        block_align = int(self.channel_cnt * self.bits_per_smaple//8)
        return block_align

    
    def get_dict(self)->dict:
        return dict(
            size            = self.size,
            audio_format    = self.audio_format,
            channel_cnt     = self.channel_cnt,
            sample_rate     = self.sample_rate,
            byte_rate       = self.byte_rate,
            block_align     = self.block_align,
            bits_per_smaple = self.bits_per_smaple
        )


WavHeaderConstructGen = Struct(
    "riff_id"   / Const(b"RIFF"),
    "size"      / Int32ul,
    "wav_id"    / Const(b"WAVE"),
)
WavHeaderConstruct = WavHeaderConstructGen.compile()


WavDataConstructGen = Struct(
    "data_id"   / Const(b"data"),
    "size"      / Int32ul
)
WavDataConstruct = WavDataConstructGen.compile()