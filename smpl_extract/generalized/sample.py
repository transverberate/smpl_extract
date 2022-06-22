import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

import copy
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
import enum
from io import IOBase
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from midi import MidiNote


class ChannelConfig(enum.IntEnum):
    MONO = enum.auto()
    STEREO_SINGLE_STREAM = enum.auto()
    STEREO_SPLIT_STREAMS = enum.auto()


class Endianness(enum.IntEnum):
    LITTLE  = enum.auto()
    BIG     = enum.auto()


class Inclusivity(enum.IntEnum):
    INCLUSIVE   = enum.auto()
    EXCLUSIVE   = enum.auto()


class LoopType(enum.IntEnum):
    FORWARD     = enum.auto()
    ALTERNATING = enum.auto()
    REVERSE     = enum.auto()


@dataclass
class LoopRegion:
    start_sample:   int = 0
    end_sample:     int = 0
    loop_type:      LoopType = LoopType.FORWARD
    start_include:  Inclusivity = Inclusivity.INCLUSIVE
    end_include:    Inclusivity = Inclusivity.INCLUSIVE
    repeat_forever: bool = True
    play_cnt:       Optional[int] = None
    duration:       Optional[float] = None


@dataclass
class Sample:
    name:               str = ""
    path:               List[str] = field(default_factory=list)
    channel_config:     ChannelConfig = ChannelConfig.MONO
    endianness:         Endianness = Endianness.LITTLE
    sample_rate:        int = 44100
    bytes_per_sample:   int = 2
    num_channels:       int = 1
    num_audio_samples:  Optional[int] =  None
    data_streams:       List[IOBase] = field(default_factory=list)
    loop_regions:       List[LoopRegion] = field(default_factory=list)
    midi_note:          Optional[MidiNote] = None
    pitch_offset_semi:  Optional[int] = None
    pitch_offset_cents: Optional[int] = None

    def __post_init__(self):
        self.original_path = self.path.copy()


def combine_stereo(left: Sample, right: Sample, new_name: Optional[str] = None) -> Sample:
    dict_copy = dict(
        (field.name, copy.copy(getattr(left, field.name)))
        for field in fields(left)
    )
    result = Sample(**dict_copy)
    result.data_streams += right.data_streams
    result.channel_config = ChannelConfig.STEREO_SPLIT_STREAMS
    result.num_channels = len(result.data_streams)
    if new_name is not None:
        result.name = new_name
        result.path[-1] = new_name

    return result


def sort_by_directory(
        samples: List[Sample]
    ) -> Dict[Tuple[str, ...], List[Sample]]:
    result: Dict[Tuple[str, ...], List[Sample]] = dict()
    for sample in samples:
        path = sample.path
        directory: Tuple[str, ...]
        if len(path) < 2:
            directory = ()
        else:
            directory = tuple(path[:-1])
        
        if directory not in result.keys():
            result[directory] = list()
        
        result[directory].append(sample)

    return result

