import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
from io import SEEK_SET, BufferedIOBase
import math
from typing import Callable, Dict, List

from data_types import AKAI_SAMPLE_DATA_OFFSET_S1000, AKAI_SAMPLE_WORDLENGTH, LoopDataConstruct, SampleHeaderConstruct, AkaiLoopType, MidiNote, SampleType
from wav.data_types import SmpteFormat, WavFormatChunkStruct, WavLoopStruct, WavLoopType, WavSampleChunkStruct
from data_reader import DataFileStream


class LoopEntry:


    def __init__(
            self,
            loop_start: int,
            loop_end: float,
            loop_duration: float,
            repeat_forever: bool
    )->None:
        self.loop_start = loop_start
        self.loop_end = loop_end 
        self.loop_active_duration = loop_duration
        self.repeat_forever = repeat_forever

    
    @classmethod
    def from_akai_loop_data(cls, loop_data: LoopDataConstruct):
        loop_at = loop_data.loop_start
        loop_length = loop_data.loop_length_coarse
        
        loop_duration = loop_data.loop_duration
        repeat_forever = (loop_duration >= 9999)

        loop_start = (loop_at - 1) - loop_length
        if loop_start < 0:
            loop_start = 0
        loop_end = loop_at

        result = cls(
            loop_start,
             loop_end, 
             loop_duration, 
             repeat_forever
        )
        return result


class Sample:


    def __init__(
            self,
            name: str,
            sample_type: SampleType,
            sample_rate: int,
            bytes_per_sample: int,
            samples_cnt: int,
            start_sample: int,
            end_sample: int,
            note_pitch: MidiNote = None,
            pitch_cents: int = 0,
            pitch_semi: int = 0,
            loop_type: AkaiLoopType = None,
            loop_entries: List[LoopEntry] = None,
            get_reader_func: Callable[[BufferedIOBase], BufferedIOBase] = None
    ) -> None:
        self.name = name
        self.sample_type = sample_type
        self.sample_rate = sample_rate
        self.bytes_per_sample = bytes_per_sample
        self.samples_cnt = samples_cnt
        self.start_sample = start_sample
        self.end_sample = end_sample
        self.note_pitch = \
            note_pitch or MidiNote(MidiNote.ScaleDegree.C, False, 4)
        self.pitch_cents = pitch_cents
        self.pitch_semi = pitch_semi
        self.loop_type = loop_type or AkaiLoopType.LOOP_INACTIVE
        self.loop_entries = loop_entries or []
        self.get_data_reader = get_reader_func or (lambda x: None)


    def get_info(self)->Dict[str, str]:
        duration = self.samples_cnt / self.sample_rate
        result = {
            "Name":  self.name,
            "Type":  self.sample_type.to_string(),
            "Sample rate":   f"{self.sample_rate} Hz",
            "Duration": f"{duration:0.3f} sec",
            "Num. samples": f"{self.samples_cnt}",
            "Start sample": f"{self.start_sample}",
            "End sample": f"{self.end_sample}",
            "Note":  f"{self.note_pitch.to_string()}",
            "Pitch semitones": f"{self.pitch_semi}",
            "Pitch cents": f"{self.pitch_cents}",
            "Loop type": f"{self.loop_type.to_string()}"
        }
        for i, loop in enumerate(self.loop_entries):
            loop_id_str = f"Loop #{i + 1}"
            result[f"{loop_id_str} start"] = str(loop.loop_start)
            result[f"{loop_id_str} end"] = str(loop.loop_end)
        return result
    
    def get_wave_smpl_header(self)->WavSampleChunkStruct:
        loop_headers = []
        if self.loop_type != AkaiLoopType.LOOP_INACTIVE:
            for i, loop in enumerate(self.loop_entries):
                play_cnt = 0
                if not loop.repeat_forever:
                    loop_active_duration = loop.loop_active_duration
                    loop_duration = (loop.loop_end - loop.loop_start)/self.sample_rate
                    play_cnt = round(loop_active_duration/loop_duration)
                loop_headers.append(WavLoopStruct(
                    cue_id=i,
                    loop_type=WavLoopType.FORWARD,
                    start_byte=loop.loop_start,
                    end_byte=math.floor(loop.loop_end),
                    fraction=0,
                    play_cnt=play_cnt
                ))
        sample_period_nano = (10**9)/self.sample_rate
        pitch_cents_normalized = 0 # TODO, implement formula
        smpl_header = WavSampleChunkStruct(
            manufacturer=0,
            product=0,
            sample_period=round(sample_period_nano),
            midi_note=self.note_pitch,
            pitch_fraction=pitch_cents_normalized,
            smpte_format=SmpteFormat.NONE,
            smpte_offset=0,
            sample_loops=loop_headers,
            sampler_data=b""
        )
        return smpl_header


    @classmethod
    def from_raw_stream(
        cls,
        partition_segment: BufferedIOBase,
        get_file_stream: Callable[[BufferedIOBase], BufferedIOBase],
    ):
        header = SampleHeaderConstruct.parse_stream(partition_segment)

        # parse loop entries
        loop_entries = []
        if header.loop_type != AkaiLoopType.LOOP_INACTIVE:
            for loop_data in header.loop_data_table:
                loop_duration = loop_data.loop_duration
                if loop_duration > 0:
                    loop_entries.append(LoopEntry.from_akai_loop_data(loop_data))

        # function for data stream
        def get_data_stream(
                partition_segment_inner: BufferedIOBase
        )->BufferedIOBase:

            filesize = AKAI_SAMPLE_WORDLENGTH * header.samples_cnt
            file_reader = DataFileStream(
                get_file_stream(partition_segment_inner),
                AKAI_SAMPLE_DATA_OFFSET_S1000,
                filesize
            )
            return file_reader

        result = cls(
            header.name,
            header.id,
            header.sampling_rate,
            AKAI_SAMPLE_WORDLENGTH,
            header.samples_cnt,
            header.play_start,
            header.play_end,
            header.note_pitch,
            header.pitch_offset_cents,
            header.pitch_offset_semi,
            header.loop_type,
            loop_entries,
            get_data_stream
        )
        
        return result
        