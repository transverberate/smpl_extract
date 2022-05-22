import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from akai.image import InvalidPathStr
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from io import IOBase
from io import SEEK_END
from io import SEEK_SET
from typing import List

from cuesheet import CueSheetFile
import util.dataclass
from util.stream import StreamOffset


SAMPLE_WIDTH = 2
SAMPLING_RATE = 44100
N_CHANNELS = 2
SAMPLES_PER_FRAME = 588
BYTES_PER_FRAME = SAMPLE_WIDTH * N_CHANNELS * SAMPLES_PER_FRAME


@dataclass
class AudioTrack:
    title: str = ""
    data_stream: IOBase = field(default_factory=IOBase)

    @property
    def name(self):
        return self.title

    @property
    def type(self):
        return "CD Audio Track"

    def itemize(self):
        items = {
            k.name: getattr(self, k.name) 
            for k in fields(self) if k.name != "data_stream"
        }
        result = util.dataclass.itemize(items)
        return result


@dataclass
class CompactDiskAudioImage:
    tracks: List[AudioTrack] = field(default_factory=list)

    @property
    def children(self):
        tracks_dict = {
            x.title: x for x in self.tracks
        }
        return tracks_dict

    def get_node_from_path(self, path: str):
        if len(path.strip()):
            raise InvalidPathStr("Paths strings not valid for CD Audio Images")
        return self


class CompactDiskAudioImageAdapter:

    @classmethod
    def from_bin_cue(
            cls, 
            bin_file_stream: IOBase,
            cue_file: CueSheetFile
    ):
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

                    offset_bytes = BYTES_PER_FRAME*cur_n_frames
                    size_bytes = BYTES_PER_FRAME*(next_n_frames - cur_n_frames)

                    data_stream = StreamOffset(
                        bin_file_stream,
                        size_bytes,
                        offset_bytes
                    )

                    audio_track = AudioTrack(
                        title,
                        data_stream
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

                data_stream = StreamOffset(
                        bin_file_stream,
                        size_bytes,
                        offset_bytes
                    )

                audio_track = AudioTrack(
                    title,
                    data_stream
                )
                audio_tracks.append(audio_track)

        result = CompactDiskAudioImage(audio_tracks)
        return result

