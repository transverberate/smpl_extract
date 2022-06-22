import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct import Adapter
from construct import Container 
from io import IOBase
import numpy as np
from typing import List
from typing import  Tuple

from formats.wav import RiffStruct
from formats.wav import SmpteFormat
from formats.wav import WavFormatChunkContainer
from formats.wav import WavLoopContainer
from formats.wav import WavLoopType
from formats.wav import WavRiffChunkType
from formats.wav import WavSampleChunkContainer
from generalized.sample import ChannelConfig
from generalized.sample import LoopType
from generalized.sample import Sample
from midi import MidiNote
from util.stream import SectorReadError


class UnexpectedNumberOfChannels(Exception): ...
class NoDataStream(Exception): ...


def get_fmt_chunk_data(sample: Sample) -> WavFormatChunkContainer:
    result = WavFormatChunkContainer(
        audio_format=1,
        channel_cnt=sample.num_channels,
        sample_rate=sample.sample_rate,
        bits_per_sample=8*sample.bytes_per_sample,
    )
    return result


def get_smpl_normalized_pitch(semi: int, cents: int) -> Tuple[int, int]:
    CENTS_DIV = float(0x80000000) / 50

    comb_cents = 50*semi + cents
    note_offset = round((comb_cents) // 100)
    cents_offset = (comb_cents) % 100
    cents_normalized = int(round(cents_offset * CENTS_DIV))

    result = (note_offset, cents_normalized)
    return result


_DEFAULT_SAMPLE_RATE = 44100
def get_smpl_chunk_data(sample: Sample) -> WavSampleChunkContainer:
    
    sample_rate = sample.sample_rate
    if sample_rate == 0:
        sample_rate = _DEFAULT_SAMPLE_RATE

    loop_type_mapping = {
        LoopType.FORWARD:       WavLoopType.FORWARD,
        LoopType.ALTERNATING:   WavLoopType.ALTERNATING,
        LoopType.REVERSE:       WavLoopType.REVERSE
    }

    loop_headers = []
    if len(sample.loop_regions):
        for i, loop in enumerate(sample.loop_regions):
            play_cnt = 0
            if loop.play_cnt is not None:
                play_cnt = loop.play_cnt
            elif not loop.repeat_forever and loop.duration is not None:
                loop_duration = loop.duration
                loop_total_duration = (loop.end_sample - loop.start_sample)/sample_rate
                if loop_total_duration == 0: 
                    continue
                play_cnt = round(loop_duration/loop_total_duration)

            loop_type = loop_type_mapping.get(
                loop.loop_type,
                WavLoopType.FORWARD
            )
            
            loop_headers.append(WavLoopContainer(
                cue_id=i,
                loop_type=loop_type,
                start_byte=loop.start_sample,
                end_byte=loop.end_sample,
                fraction=0,
                play_cnt=play_cnt
            ))
    sample_period_nano = (10**9)/sample_rate

    pitch_semi = sample.pitch_offset_semi or 0
    pitch_cents = sample.pitch_offset_cents or 0
    note_pitch_offset, pitch_cents_normalized = get_smpl_normalized_pitch(
        pitch_semi,
        pitch_cents
    )
    midi_note = sample.midi_note or MidiNote.from_string("C4")
    adj_note_pitch = MidiNote.from_midi_byte(
        midi_note.to_midi_byte() + note_pitch_offset
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


_BUFFER_SIZE = 0x1000
def sample_frame_gen_simple(data_stream: IOBase):
    while True:
        buffer = data_stream.read(_BUFFER_SIZE)
        if len(buffer) < 1:
            break
        yield buffer


def sample_frame_gen_interleaved(
        data_streams: List[IOBase]
):

    if 2 > len(data_streams) < 0:
        raise UnexpectedNumberOfChannels(
            f"{len(data_streams)} channels not supported"
        )  

    buffer = [bytes()]*len(data_streams)
    continue_flag = True
    while continue_flag:
        for i, data_stream in enumerate(data_streams):
            if data_stream is None:
                continue
            try:
                buffer[i] = data_stream.read(_BUFFER_SIZE)
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


class WavSampleAdapter(Adapter):
    
    def _encode(self, obj: Sample, context, path) -> Container:
        del path  # Unused
        sample = obj

        riff_chunks = []

        # fmt chunk
        riff_chunks.append(Container({
            "riff_id":  WavRiffChunkType.FMT,
            "data":     get_fmt_chunk_data(sample)
        }))

        # smpl chunk
        requires_smpl_chunk = any((x is not None for x in (
                sample.midi_note, 
                sample.pitch_offset_cents, 
                sample.pitch_offset_semi
            ))) or len(sample.loop_regions) > 0
        
        if requires_smpl_chunk:
            riff_chunks.append(Container({
                "riff_id":  WavRiffChunkType.SMPL,
                "data":     get_smpl_chunk_data(sample)
            }))

        # data chunk
        if len(sample.data_streams) < 1:
            raise NoDataStream("Sample has no data stream")

        if sample.channel_config == ChannelConfig.STEREO_SPLIT_STREAMS:
            data_gen = sample_frame_gen_interleaved(sample.data_streams)
        else:
            data_gen = sample_frame_gen_simple(sample.data_streams[0])

        riff_chunks.append(Container({
            "riff_id":  WavRiffChunkType.DATA,
            "data":     data_gen
        }))

        result = Container({
            "data": Container({
                "chunks": riff_chunks
            })
        })
        return result
        

    def _decode(self, obj, context, path):
        raise NotImplementedError


WavSampleBuilder = WavSampleAdapter(RiffStruct)


def export_wav(sample: Sample, file_path: str):
    with open(file_path, "wb") as export_stream:
        WavSampleBuilder.build_stream(sample, export_stream)
    return

