from io import BufferedIOBase, BufferedWriter, FileIO
import io, os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
import math
from typing import List, Union
from collections import abc
from wav.data_types import WavDataConstruct, WavFormatChunkStruct, WavHeaderConstruct
import wave
import numpy as np

from akai.sample import Sample


BUFFER_SIZE = 0x4000


def _write_wav_headers(channels: List[Sample], stream):

    master_channel = channels[0]
    fmt_header = WavFormatChunkStruct(
        audio_format=1,
        channel_cnt=len(channels),
        sample_rate=master_channel.sample_rate,
        bits_per_smaple=master_channel.bytes_per_sample*8
    ).build()
    smpl_header = master_channel.get_wave_smpl_header().build()
    data_size = master_channel.samples_cnt * master_channel.bytes_per_sample * len(channels)
    data_header = WavDataConstruct.build(dict(size=data_size))
    riff_size = len(smpl_header) + len(fmt_header) + len(data_header) + data_size + 4
    riff_header = WavHeaderConstruct.build(dict(size=riff_size))

    stream.write(riff_header)
    stream.write(fmt_header)
    stream.write(smpl_header)
    stream.write(data_header)


def write_wave_from_samples(
        image_file: BufferedIOBase,
        output_stream: BufferedWriter,
        channels: Union[List[Sample], Sample]
):
    if not isinstance(channels, abc.Iterable):
        channels = [channels]

    if 2 > len(channels) < 0:
        raise Exception(f"{len(channels)} not supported")  
    
    _write_wav_headers(channels, output_stream)
    readers = list(map(lambda x: x.get_data_reader(image_file), channels))

    buffer = [bytes()]*len(channels)
    continue_flag = True
    while continue_flag:
        for i, reader in enumerate(readers):
            buffer[i] = reader.read(BUFFER_SIZE)
            if len(buffer[i]) < 1:
                continue_flag = False
                break
        if continue_flag:
            if len(buffer) == 1:
                output_stream.write(buffer[0])
            else:
                comb = np.vstack(( 
                    np.frombuffer(buffer[0], "int16"), 
                    np.frombuffer(buffer[1], "int16")
                )).reshape((-1,),order='F').tobytes()
                output_stream.write(comb)
        
    return
                




