import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
import numpy as np
from typing import Callable
from typing import List
from typing import Tuple

from data_streams import DataStream
from data_streams import NoDataStream
from data_streams import IncompatibleNumberOfChannels
from data_streams import StreamEncoding
from data_streams import system_byte_order
from util.stream import SectorReadError


_DEFAULT_BUFFER_SIZE = 0x1000


def get_num_frames_possible(
        stream: DataStream, 
        target_size: int = _DEFAULT_BUFFER_SIZE
) -> int:
    frame_size = stream.frame_size
    num_frames = max(1, target_size // frame_size)
    return num_frames


def get_buffer_sizes(streams: List[DataStream]) -> List[int]:
    num_frames = min(list(get_num_frames_possible(x) for x in streams))
    buffer_sizes = list(num_frames * x.frame_size for x in streams)
    return buffer_sizes


def pad_channels(channels: List[np.ndarray]) -> List[np.ndarray]:
    target_size = max(map(len, channels))
    result_channels = []
    for channel in channels:
        N = target_size - len(channel)
        if N <= 0:
            result_channels.append(channel)
            continue

        padded_channel = np.pad(
            channel, 
            (0, N), 
            "linear_ramp", 
            end_values=(0, 0)
        )
        result_channels.append(padded_channel)
    return result_channels


def decode_frame(
        streams: List[DataStream], 
        buffer_sizes: List[int]
) -> List[np.ndarray]:

    channels: List[np.ndarray] = []

    for stream, size in zip(streams, buffer_sizes):
        dtype = stream.encoding.dtype
        num_channels = max(1, stream.encoding.num_interleaved_channels)
        buffer = stream.stream.read(size)

        if buffer is None or len(buffer) <= 0:
            for i in range(num_channels):
                channels.append(np.zeros(0, dtype=dtype))
            continue
        
        samples_interleaved: np.ndarray = np.frombuffer(buffer, dtype=dtype)
        samples = [samples_interleaved]
        if num_channels > 1:
            samples_arr = samples_interleaved.reshape((-1, num_channels)).T
            samples = list(samples_arr)

        channels += samples

    return channels


def encode_frame(channels: List[np.ndarray], dest_dtype: np.dtype) -> bytes:
    channels = pad_channels(channels)
    channels = list(x.astype(dest_dtype) for x in channels)
    result = np.vstack(channels).reshape((-1,), order='F').tobytes()
    return result


def swap_endianess(channels: List[np.ndarray]) -> List[np.ndarray]:
    result = list(x.byteswap() for x in channels)
    return result


def swap_endianess_multi(
        channels: List[np.ndarray], 
        swaps: List[bool]
) -> List[np.ndarray]:
    result_channels = []
    for channel, swap in zip(channels, swaps):
        if swap:
            result_channels.append(channel.byteswap())
            continue
        result_channels.append(channel)
    return result_channels


@dataclass
class PassthroughTranscoder:
    data_stream: DataStream 
    buffer_size: int = _DEFAULT_BUFFER_SIZE


    def __iter__(self):
        return self


    def __next__(self):
        stream = self.data_stream.stream
        try:
            buffer = stream.read(self.buffer_size)
        except SectorReadError as e:
            raise StopIteration
        if len(buffer) <= 0:
            raise StopIteration
        return buffer


@dataclass
class TranscodePipelineStruct:
    f_decode:       Callable[[List[DataStream]], List[np.ndarray]] 
    processes:      List[Tuple[
            str, 
            Callable[[List[np.ndarray]], List[np.ndarray]]
        ]]
    f_encode:       Callable[[List[np.ndarray]], bytes]


@dataclass
class PipelineTranscoder:
    data_streams: List[DataStream]
    pipeline: TranscodePipelineStruct


    def __iter__(self):
        return self


    def __next__(self):
        try:
            channels = self.pipeline.f_decode(self.data_streams)
        except SectorReadError:  # TODO: Create more robust handling for this
            raise StopIteration
        if any(len(x) <= 0 for x in channels):
            raise StopIteration

        for process in self.pipeline.processes:
            f_process = process[1]
            channels = f_process(channels)
        
        result = self.pipeline.f_encode(channels)
        return result


def make_transcoder(
        data_streams: List[DataStream],
        dest_encoding: StreamEncoding
    ):
    
    # check for bad args
    if len(data_streams) <= 0:
        raise NoDataStream("No data streams given")

    total_num_channels = 0
    for data_stream in data_streams:
        num_channels = max(1, data_stream.encoding.num_interleaved_channels)
        total_num_channels += num_channels
    expected_num_channels = dest_encoding.num_interleaved_channels
    if total_num_channels != expected_num_channels:
        raise IncompatibleNumberOfChannels(
            f"Expected {expected_num_channels} fourd {total_num_channels}."
        )
    
    # begin
    buffer_sizes = get_buffer_sizes(data_streams)

    if len(data_streams) == 1 \
            and data_streams[0].encoding == dest_encoding:
        result = PassthroughTranscoder(
            data_streams[0], 
            buffer_size=buffer_sizes[0]
        )
        return result

    processes: List[Tuple[
        str,
        Callable[[List[np.ndarray]], List[np.ndarray]]
    ]]
    processes = []

    # is byteswap needed at input?
    swaps = list(
        x.encoding.endianess != system_byte_order for x in data_streams
    )
    if any(swaps):
        if all(swaps):
            processes.append(("swap_input_endianess", swap_endianess))
        else:
            processes.append((
                "swap_input_endianess_multi", 
                lambda x: swap_endianess_multi(x, swaps)
            ))
    
    # is byte swap needed at output?
    if dest_encoding.endianess != system_byte_order:
        processes.append(("swap_output_endianess", swap_endianess))

    dest_dtype = dest_encoding.dtype

    f_decode_frame = lambda x: decode_frame(x, buffer_sizes=buffer_sizes)
    f_encode_frame = lambda x: encode_frame(x, dest_dtype=dest_dtype)
    pipeline = TranscodePipelineStruct(
        f_decode_frame, 
        processes, 
        f_encode_frame
    )

    result = PipelineTranscoder(data_streams, pipeline)
    return result

