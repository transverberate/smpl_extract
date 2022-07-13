import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from construct.core import Adapter
from construct.core import Pass
from dataclasses import dataclass
from dataclasses import field
from io import IOBase
from typing import Any
from typing import cast
from typing import ClassVar
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

from base import Element
from data_streams import DataStream
from data_streams import Endianess
from data_streams import StreamEncoding
from .data_types import RolandLoopMode
from .data_types import ROLAND_SAMPLE_WIDTH
from generalized.sample import ChannelConfig
from generalized.sample import LoopRegion
from generalized.sample import LoopType
from generalized.sample import Sample
from .patch_entry import PatchEntry
from .sample_entry import SampleEntry
from .sample_entry import SampleParamCommon
from .sample_entry import SampleParamOptionsSection
from structural import SampleElement
from util.constructs import ChildInfo
from util.constructs import ElementAdapter
from util.dataclass import get_common_field_args
from util.stream import StreamOffset
from util.stream import StreamReversed


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
        end_sample=sustain_end,
        repeat_forever=False
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
        repeat_forever=False,
        loop_type=LoopType.ALTERNATING
    )

    result = SampleParams(
        stream_result,
        loops=[sustain_loop]
    )
    return result


def _get_reverse_oneshot_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    offset_sample = points.start
    num_samples = points.sustain_end - offset_sample + 1
    stream_size = ROLAND_SAMPLE_WIDTH * num_samples

    stream_result = StreamReversed(
        StreamOffset(
            stream,
            stream_size,
            ROLAND_SAMPLE_WIDTH * offset_sample
        ),
        stream_size,
        sample_width=ROLAND_SAMPLE_WIDTH
    )

    result = SampleParams(
        stream_result,
        loops=[]
    )
    return result


def _get_reverse_loop_params(
        stream: IOBase, 
        points: RolandLoopPoints
) -> SampleParams:
    offset_sample = points.start
    num_samples = points.sustain_end - offset_sample + 1
    stream_size = ROLAND_SAMPLE_WIDTH * num_samples

    stream_result = StreamReversed(
        StreamOffset(
            stream,
            stream_size,
            ROLAND_SAMPLE_WIDTH * offset_sample
        ),
        stream_size,
        sample_width=ROLAND_SAMPLE_WIDTH
    )

    loop_start   = max(0, points.sustain_end - points.start)
    loop_end     = max(0, points.sustain_end - points.sustain_start)

    sustain_loop = LoopRegion(
        start_sample=loop_start,
        end_sample=loop_end,
        repeat_forever=True
    )
    result = SampleParams(
        stream_result,
        loops=[sustain_loop]
    )
    return result


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


    def to_generalized(self) -> Sample:

        points = RolandLoopPoints(
            self.start_sample.address,
            self.sustain_loop_start.address,
            self.sustain_loop_end.address,
            self.release_loop_start.address,
            self.release_loop_end.address
        )

        get_params_map = {
            RolandLoopMode.FORWARD_END:       _get_forward_end_params,
            RolandLoopMode.FORWARD_RELEASE:   _get_forward_release_params,
            RolandLoopMode.ONESHOT:           _get_oneshot_params,
            RolandLoopMode.FORWARD_ONESHOT:   _get_forward_oneshot_params,
            RolandLoopMode.ALTERNATE:         _get_alternate_params,
            RolandLoopMode.REVERSE_ONESHOT:   _get_reverse_oneshot_params,
            RolandLoopMode.REVERSE_LOOP:      _get_reverse_loop_params,
        }
        
        f_get_params = get_params_map.get(
            self.loop_mode,
            _get_forward_end_params
        )

        data_stream, loop_regions = f_get_params(
            self._data_stream,
            points
        )

        stream_encoding = StreamEncoding(
            endianess=Endianess.LITTLE, 
            sample_width=self.bytes_per_sample, 
            num_interleaved_channels=1
        )
        data_streams = [
            DataStream(stream=data_stream, encoding=stream_encoding)
        ]
        result = Sample(
            name=self.name,
            channel_config=ChannelConfig.MONO,
            sample_rate=self.sampling_frequency,
            num_channels=1,
            midi_note=self.original_key,
            pitch_offset_semi=0,
            pitch_offset_cents=0,
            loop_regions=loop_regions,
            data_streams=data_streams,
            _parent=self.parent,
            _path=self.path,
            _safe_name=self.safe_name,
            _export_name=self.export_name
        )
        return result
    

class SampleFileAdapter(ElementAdapter):

    def _decode_element(
                self, 
                obj, 
                child_info: ChildInfo, 
                context: Dict[str, Any], 
                path: str
        ):
        del context, path  # unused

        sample_entry = cast(SampleEntry, obj)

        parent = child_info.parent
        element_path = child_info.parent_path
        
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

        sample_files = {}
        for partial_entry in patch_entry.partial_entries:
            for sample_entry in partial_entry.sample_entries:
                if sample_entry.index not in sample_files.keys():
                    sample_file = sc._decode(sample_entry, context, path)
                    sample_files[sample_entry.index] = sample_file

        return list(sample_files.values())


    def _encode(self, obj, context, path):
        raise NotImplementedError

