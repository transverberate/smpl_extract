import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from collections import abc
from construct.core import Adapter
from construct.lib.containers import Container
import math
import numpy as np
from typing import List
from typing import Tuple
from typing import Union

from .base import RiffStruct
from .base import SmpteFormat
from .base import WavFormatChunkContainer
from .base import WavLoopContainer
from .base import WavLoopType
from .base import WavRiffChunkType
from .base import WavSampleChunkContainer
from akai.data_types import AkaiLoopType
from akai.sample import Sample
from midi import MidiNote
from util.stream import SectorReadError


def get_fmt_chunk_data(channels: List[Sample])->WavFormatChunkContainer:

    master_channel = channels[0]
    result = WavFormatChunkContainer(
        audio_format=1,
        channel_cnt=len(channels),
        sample_rate=master_channel.sample_rate,
        bits_per_sample=master_channel.bytes_per_sample*8,
    )
    return result


def get_smpl_normalized_pitch(semi: int, cents: int)->Tuple[int, int]:
    CENTS_DIV = float(0x80000000) / 50

    comb_cents = 50*semi + cents
    note_offset = round((comb_cents) // 100)
    cents_offset = (comb_cents) % 100
    cents_normalized = int(round(cents_offset * CENTS_DIV))

    result = (note_offset, cents_normalized)
    return result


_DEFAULT_SAMPLE_RATE = 44100
def get_smpl_chunk_data(channels: List[Sample])->WavSampleChunkContainer:
    
    master_channel = channels[0]
    sample_rate = master_channel.sample_rate
    if sample_rate == 0:
        sample_rate = _DEFAULT_SAMPLE_RATE

    loop_headers = []
    if master_channel.loop_type != AkaiLoopType.LOOP_INACTIVE:
        for i, loop in enumerate(master_channel.loop_entries):
            play_cnt = 0
            if not loop.repeat_forever:
                loop_duration = loop.loop_duration
                loop_total_duration = (loop.loop_end - loop.loop_start)/sample_rate
                if loop_total_duration == 0: 
                    continue
                play_cnt = round(loop_duration/loop_total_duration)
            loop_headers.append(WavLoopContainer(
                cue_id=i,
                loop_type=WavLoopType.FORWARD,
                start_byte=loop.loop_start,
                end_byte=math.floor(loop.loop_end),
                fraction=0,
                play_cnt=play_cnt
            ))
    sample_period_nano = (10**9)/sample_rate
    note_pitch_offset, pitch_cents_normalized = get_smpl_normalized_pitch(
        master_channel.pitch_semi,
        master_channel.pitch_cents
    )
    adj_note_pitch = MidiNote.from_midi_byte(
        master_channel.note_pitch.to_midi_byte() + note_pitch_offset
    )
    smpl_header = WavSampleChunkContainer(
        manufacturer=0,
        product=0,
        sample_period=round(sample_period_nano),
        midi_note=adj_note_pitch,
        pitch_fraction=pitch_cents_normalized,
        smpte_format=SmpteFormat.NONE,
        smpte_offset=0,
        sample_loops=loop_headers,
        sampler_data=b""
    )
    return smpl_header


BUFFER_SIZE = 0x1000


def wave_data_generator(
        channels: Union[List[Sample], Sample]
):
    if not isinstance(channels, abc.Iterable):
        channels = [channels]

    if 2 > len(channels) < 0:
        raise Exception(f"{len(channels)} not supported")  
    
    readers = list(map(lambda x: x.data_stream, channels))

    buffer = [bytes()]*len(channels)
    continue_flag = True
    while continue_flag:
        for i, reader in enumerate(readers):
            if reader is None:
                continue
            try:
                buffer[i] = reader.read(BUFFER_SIZE)
            except SectorReadError:
                # TODO: Create more robust handling for this
                continue_flag = False
                break
            if len(buffer[i]) < 1:
                continue_flag = False
                break
        if continue_flag:
            if len(buffer) == 1:
                yield buffer[0]
            else:
                left    = np.frombuffer(buffer[0], "int16")
                right   = np.frombuffer(buffer[1], "int16")

                if len(left) < len(right):
                    N = len(right) - len(left)
                    left = np.pad(left, (0, N), "linear_ramp", end_values=(0, 0))
                elif len(right) < len(left):
                    N = len(left) - len(right)
                    right = np.pad(right, (0, N), "linear_ramp", end_values=(0, 0))

                comb = np.vstack(( 
                    left, 
                    right
                )).reshape((-1,),order='F').tobytes()
                yield comb
    return


class WavAkaiSampleAdapter(Adapter):
    
    def _encode(self, obj: List[Sample], context, path)->Container:
        del path  # Unused
        samples = obj 

        fmt_chunk = Container({
            "riff_id":  WavRiffChunkType.FMT,
            "data":     get_fmt_chunk_data(samples)
        })
        smpl_chunk = Container({
            "riff_id":  WavRiffChunkType.SMPL,
            "data":     get_smpl_chunk_data(samples)
        })
        data_chunk = Container({
            "riff_id":  WavRiffChunkType.DATA,
            "data":     wave_data_generator(samples)
        })

        result = Container({
            "data": Container({
                "chunks": [
                    fmt_chunk,
                    smpl_chunk,
                    data_chunk
                ]
            })
        })
        return result
        

    def _decode(self, obj, context, path):
        raise NotImplementedError


WavAkaiSampleStruct = WavAkaiSampleAdapter(RiffStruct)

