import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
from dataclasses import field
from io import IOBase
from io import SEEK_END
from io import SEEK_SET
from typing import ClassVar
from typing import List
from typing import Optional

from smpl_extract.base import Element
from cuesheet import CueSheetFile
from generalized.sample import ChannelConfig
from generalized.sample import Endianness
from generalized.sample import Sample
from structural import Image
from structural import SampleElement
from util.stream import StreamOffset


SAMPLE_WIDTH = 2
SAMPLING_RATE = 44100
N_CHANNELS = 2
SAMPLES_PER_FRAME = 588
BYTES_PER_FRAME = SAMPLE_WIDTH * N_CHANNELS * SAMPLES_PER_FRAME


@dataclass
class AudioTrack(SampleElement):
    title: str = ""
    num_channels:       int = 2
    sample_rate:        int = 44100
    bytes_per_sample:   int = 2
    num_audio_samples:  int = 0
    _data_stream:       IOBase = field(default_factory=IOBase)
    _parent:            Optional[Element] = None
    _path:              List[str] = field(default_factory=list)

    type_name: ClassVar[str] = "CDDA Track"


    @property
    def name(self):
        return self.title


    def to_generalized(self) -> Sample:
        data_streams = [self._data_stream]
        result = Sample(
            name=self.name,
            channel_config=ChannelConfig.STEREO_SINGLE_STREAM,
            endianness=Endianness.LITTLE,
            sample_rate=self.sample_rate,
            bytes_per_sample=self.bytes_per_sample,
            num_channels=2,
            num_audio_samples=self.num_audio_samples,
            data_streams=data_streams,
            _path=self.path
        )
        return result


@dataclass
class CompactDiskAudioImage(Image):
    tracks: List[AudioTrack] = field(default_factory=list)
    _path: ClassVar[List[str]] = []
    _parent: ClassVar[Optional[Element]] = None
    name: ClassVar[str] = "CDDA Image"
    type_name: ClassVar[str] = "CDDA Image"

    @property
    def children(self):
        return self.tracks


class CompactDiskAudioImageAdapter:


    @classmethod
    def from_bin_cue(
            cls, 
            bin_file_stream: IOBase,
            cue_file: CueSheetFile
    ):
        image = CompactDiskAudioImage()
        element_path = image.path

        bin_file_stream.seek(0, SEEK_END)
        end_of_file = bin_file_stream.tell()
        bin_file_stream.seek(0, SEEK_SET)

        audio_tracks = []
        cue_track_list = [x for x in cue_file.tracks if x.mode.lower() == "audio"]
        if len(cue_track_list):

            cue_track_iter = iter(cue_track_list)
            i = 0
            cur_cue_track = next(cue_track_iter)
            while True:
                try:
                    next_cue_track = next(cue_track_iter)
                except StopIteration:
                    break

                if len(cur_cue_track.indices) and len(next_cue_track.indices):
                    title = cur_cue_track.title or f"Untitled Track {i+1}"

                    cur_index = cur_cue_track.indices[0]
                    cur_n_frames = cur_index.get_total_audio_frames()
                    next_index = next_cue_track.indices[0]
                    next_n_frames = next_index.get_total_audio_frames()
                    total_n_frames = next_n_frames - cur_n_frames

                    offset_bytes = BYTES_PER_FRAME*cur_n_frames
                    size_bytes = BYTES_PER_FRAME*total_n_frames

                    total_num_samples = SAMPLES_PER_FRAME*total_n_frames

                    data_stream = StreamOffset(
                        bin_file_stream,
                        size_bytes,
                        offset_bytes
                    )

                    track_path = element_path + [title]

                    audio_track = AudioTrack(
                        title=title,
                        num_audio_samples=total_num_samples,
                        _data_stream=data_stream,
                        _parent=image,
                        _path=track_path
                    )
                    audio_tracks.append(audio_track)
                    
                    i += 1
                    cur_cue_track = next_cue_track
            
            if len(cur_cue_track.indices):
                title = cur_cue_track.title or f"Untitled Track {i+1}"

                cur_index = cur_cue_track.indices[0]
                cur_n_frames = cur_index.get_total_audio_frames()
                offset_bytes = BYTES_PER_FRAME*cur_n_frames
                size_bytes = end_of_file - offset_bytes

                total_n_frames = (size_bytes // BYTES_PER_FRAME)
                total_num_samples = SAMPLES_PER_FRAME*total_n_frames

                data_stream = StreamOffset(
                        bin_file_stream,
                        size_bytes,
                        offset_bytes
                    )

                track_path = element_path + [title]

                audio_track = AudioTrack(
                    title=title,
                    num_audio_samples=total_num_samples,
                    _data_stream=data_stream,
                    _parent=image,
                    _path=track_path
                )
                audio_tracks.append(audio_track)

        image.tracks = audio_tracks
        return image

