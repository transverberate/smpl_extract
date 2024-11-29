from construct import Adapter
from construct import Container
from typing import  Tuple

from smpl_extract.data_streams import Endianess
from smpl_extract.data_streams import NoDataStream
from smpl_extract.data_streams import StreamEncoding
from smpl_extract.formats.wav import RiffStruct
from smpl_extract.formats.wav import SmpteFormat
from smpl_extract.formats.wav import WavFormatChunkContainer
from smpl_extract.formats.wav import WavLoopContainer
from smpl_extract.formats.wav import WavLoopType
from smpl_extract.formats.wav import WavRiffChunkType
from smpl_extract.formats.wav import WavSampleChunkContainer
from smpl_extract.generalized.sample import LoopType
from smpl_extract.generalized.sample import Sample
from smpl_extract.midi import MidiNote
from smpl_extract.transcoder import make_transcoder


def get_fmt_chunk_data(sample: Sample, encoding: StreamEncoding) -> WavFormatChunkContainer:
    result = WavFormatChunkContainer(
        audio_format=1,
        channel_cnt=encoding.num_interleaved_channels,
        sample_rate=sample.sample_rate,
        bits_per_sample=8*encoding.sample_width
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


class WavSampleAdapter(Adapter):
    
    def _encode(self, obj: Sample, context, path) -> Container:
        del context, path  # Unused
        sample = obj

        if len(sample.data_streams) < 1:
            raise NoDataStream("Sample has no data stream")

        dest_encoding = StreamEncoding(
            endianess=Endianess.LITTLE,  # WAV Specification
            sample_width=sample.data_streams[0].encoding.sample_width,
            num_interleaved_channels=sample.num_channels
        )

        riff_chunks = []

        # fmt chunk
        riff_chunks.append(Container({
            "riff_id":  WavRiffChunkType.FMT,
            "data":     get_fmt_chunk_data(sample, dest_encoding)
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
        data_generator = make_transcoder(sample.data_streams, dest_encoding)
        riff_chunks.append(Container({
            "riff_id":  WavRiffChunkType.DATA,
            "data":     data_generator
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

