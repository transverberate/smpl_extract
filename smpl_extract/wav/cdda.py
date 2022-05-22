import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct.core import Adapter
from construct.lib.containers import Container
from io import IOBase

from .base import RiffStruct
from .base import WavFormatChunkContainer
from .base import WavRiffChunkType
from cdda.cdda import AudioTrack
from cdda.cdda import N_CHANNELS
from cdda.cdda import SAMPLE_WIDTH
from cdda.cdda import SAMPLING_RATE


BUFFER_SIZE = 0x1000
def wave_data_generator(data_stream: IOBase):
    while True:
        buffer = data_stream.read(BUFFER_SIZE)
        if len(buffer) < 1:
            break
        yield buffer


class WavCddaSampleAdapter(Adapter):


    def _encode(self, obj: AudioTrack, context, path)->Container:
        del path, context  # Unused
        track = obj 

        fmt_chunk = Container({
            "riff_id":  WavRiffChunkType.FMT,
            "data":     WavFormatChunkContainer(
                audio_format=1,
                channel_cnt=N_CHANNELS,
                sample_rate=SAMPLING_RATE,
                bits_per_sample=8*SAMPLE_WIDTH,
            )
        })
        data_chunk = Container({
            "riff_id":  WavRiffChunkType.DATA,
            "data":     wave_data_generator(track.data_stream)
        })

        result = Container({
            "data": Container({
                "chunks": [
                    fmt_chunk,
                    data_chunk
                ]
            })
        })

        return result


    def _decode(self, obj, context, path):
        raise NotImplementedError


WavCddaSampleStruct = WavCddaSampleAdapter(RiffStruct)

