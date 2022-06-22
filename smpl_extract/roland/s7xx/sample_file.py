import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from construct.core import Adapter
from construct.core import Pass
from dataclasses import dataclass
from dataclasses import field
from io import IOBase
from typing import cast
from typing import ClassVar
from typing import List
from typing import NamedTuple
from typing import Optional

from base import Element
from .data_types import LoopMode
from .data_types import ROLAND_SAMPLE_WIDTH
from elements import SampleElement
from generalized.sample import ChannelConfig
from generalized.sample import Endianness
from generalized.sample import LoopRegion
from generalized.sample import Sample
from .patch_entry import PatchEntry
from .sample_entry import SampleEntry
from .sample_entry import SampleParamCommon
from .sample_entry import SampleParamOptionsSection
from util.dataclass import get_common_field_args
from util.dataclass import make_itemizable
from util.stream import StreamOffset


class RolandLoopPoints(NamedTuple):
    start:          int
    sustain_start:  int 
    sustain_end:    int
    release_start:  int
    release_end:    int


class SampleParams(NamedTuple):
    data_stream:    IOBase
    loops:          List[LoopRegion]


def _get_forward_end_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    offset_sample = points.start
    num_samples = points.sustain_end - offset_sample + 1
    stream_result = StreamOffset(
        stream,
        ROLAND_SAMPLE_WIDTH * num_samples,
        ROLAND_SAMPLE_WIDTH * offset_sample
    )

    sustain_start   = max(0, points.sustain_start - offset_sample)
    sustain_end     = max(0, points.sustain_end - offset_sample)

    sustain_loop = LoopRegion(
        start_sample=sustain_start,
        end_sample=sustain_end,
        repeat_forever=True

    )
    result = SampleParams(
        stream_result,
        loops=[sustain_loop]
    )
    return result


def _get_forward_release_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    offset_sample = points.start
    num_samples = points.release_end - offset_sample + 1
    stream_result = StreamOffset(
        stream,
        ROLAND_SAMPLE_WIDTH * num_samples,
        ROLAND_SAMPLE_WIDTH * offset_sample
    )

    sustain_start   = max(0, points.sustain_start - offset_sample)
    sustain_end     = max(0, points.sustain_end - offset_sample)
    release_start   = max(0, points.release_start - offset_sample)
    release_end     = max(0, points.release_end - offset_sample)

    sustain_loop = LoopRegion(
        start_sample=sustain_start,
        end_sample=sustain_end
    )
    release_loop = LoopRegion(
        start_sample=release_start,
        end_sample=release_end,
        repeat_forever=True
    )

    result = SampleParams(
        stream_result,
        loops=[
            sustain_loop,
            release_loop
        ]
    )
    return result


def _get_oneshot_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    offset_sample = points.start
    num_samples = points.sustain_end - offset_sample + 1
    stream_result = StreamOffset(
        stream,
        ROLAND_SAMPLE_WIDTH * num_samples,
        ROLAND_SAMPLE_WIDTH * offset_sample
    )

    result = SampleParams(
        stream_result,
        loops=[]
    )
    return result


def _get_forward_oneshot_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    offset_sample = points.start
    num_samples = points.release_end - offset_sample + 1
    stream_result = StreamOffset(
        stream,
        ROLAND_SAMPLE_WIDTH * num_samples,
        ROLAND_SAMPLE_WIDTH * offset_sample
    )

    sustain_start   = max(0, points.sustain_start - offset_sample)
    sustain_end     = max(0, points.sustain_end - offset_sample)

    sustain_loop = LoopRegion(
        start_sample=sustain_start,
        end_sample=sustain_end,
        repeat_forever=False
    )

    result = SampleParams(
        stream_result,
        loops=[sustain_loop]
    )
    return result


def _get_alternate_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    raise NotImplementedError


def _get_reverse_oneshot_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    raise NotImplementedError


def _get_reverse_loop_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    raise NotImplementedError


@make_itemizable
@dataclass
class SampleFile(
        SampleParamCommon, 
        SampleParamOptionsSection, 
        SampleElement
):
    name:               str                     = ""

    _data_stream:       IOBase                  = field(default_factory=IOBase)
    _parent:            Optional[Element]       = None
    _path:              List[str]               = field(default_factory=list)

    type_name:          ClassVar[str]           = "Roland S-7xx Sample"
    bytes_per_sample:   ClassVar[int]           = ROLAND_SAMPLE_WIDTH

    
    # needed to stop unimplemented abstract method exception
    # will be added by @make_itemizable
    def itemize(self):
        return None


    def to_generalized(self) -> Sample:

        points = RolandLoopPoints(
            self.start_sample.address,
            self.sustain_loop_start.address,
            self.sustain_loop_end.address,
            self.release_loop_start.address,
            self.release_loop_end.address
        )

        get_params_map = {
            LoopMode.FORWARD_END:       _get_forward_end_params,
            LoopMode.FORWARD_RELEASE:   _get_forward_release_params,
            LoopMode.ONESHOT:           _get_oneshot_params,
            LoopMode.FORWARD_ONESHOT:   _get_forward_oneshot_params,
            LoopMode.ALTERNATE:         _get_alternate_params,
            LoopMode.REVERSE_ONESHOT:   _get_reverse_oneshot_params,
            LoopMode.REVERSE_LOOP:      _get_reverse_loop_params,
        }
        
        f_get_params = get_params_map.get(
            self.loop_mode,
            _get_forward_end_params
        )

        data_stream, loop_regions = f_get_params(
            self._data_stream,
            points
        )

        data_streams = [data_stream]
        result = Sample(
            name=self.name,
            path=self.path,
            channel_config=ChannelConfig.MONO,
            endianness=Endianness.LITTLE,
            sample_rate=self.sampling_frequency,
            bytes_per_sample=self.bytes_per_sample,
            num_channels=1,
            midi_note=self.original_key,
            pitch_offset_semi=0,
            pitch_offset_cents=0,
            loop_regions=loop_regions,
            data_streams=data_streams
        )
        return result
    

class SampleFileAdapter(Adapter):


    def _decode(self, obj, context, path):
        sample_entry = cast(SampleEntry, obj)

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys():
            if "parent" in context._.keys():
                parent = cast(Element, context._.parent)
                element_path = parent.path
        
        name = sample_entry.name
        sample_path = element_path + [name]

        common_params = get_common_field_args(
            SampleParamCommon,
            sample_entry
        )
        options_params = get_common_field_args(
            SampleParamOptionsSection,
            sample_entry
        )
        sample_file = SampleFile(
            **common_params,
            **options_params,
            name=name,
            _data_stream=sample_entry._data_stream,
            _parent=parent,
            _path=sample_path
        )
        return sample_file


    def _encode(self, obj, context, path):
        raise NotImplementedError


class SampleFileListAdapter(Adapter):


    def _decode(self, obj, context, path):
        patch_entry = cast(PatchEntry, obj)
        sc = SampleFileAdapter(Pass)

        sample_files = []
        for partial_entry in patch_entry.partial_entries.values():
            for sample_entry in partial_entry.sample_entries:
                sample_file = sc._decode(sample_entry, context, path)
                sample_files.append(sample_file)

        return sample_files


    def _encode(self, obj, context, path):
        raise NotImplementedError

