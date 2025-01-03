import copy
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
import enum
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from smpl_extract.base import Element
from smpl_extract.base import ElementTypes
from smpl_extract.data_streams import DataStream
from smpl_extract.elements import LeafElement
from smpl_extract.midi import MidiNote


class ChannelConfig(enum.IntEnum):
    MONO = enum.auto()
    STEREO_SINGLE_STREAM = enum.auto()
    STEREO_SPLIT_STREAMS = enum.auto()


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
class Sample(LeafElement):
    name:               str = ""
    channel_config:     ChannelConfig = ChannelConfig.MONO
    sample_rate:        int = 44100
    num_channels:       int = 1
    num_audio_samples:  Optional[int] =  None
    data_streams:       List[DataStream] = field(default_factory=list)
    loop_regions:       List[LoopRegion] = field(default_factory=list)
    midi_note:          Optional[MidiNote] = None
    pitch_offset_semi:  Optional[int] = None
    pitch_offset_cents: Optional[int] = None

    _parent:            Optional[Element] = None
    _path:              List[str] = field(default_factory=list)
    _safe_name:         Optional[str] = None
    _export_name:       Optional[str] = None

    type_id:            ClassVar[ElementTypes] = ElementTypes.SampleGeneralized
    type_name:          ClassVar[str] = "Sample (Generalized)"


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
        result._export_name = new_name

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

