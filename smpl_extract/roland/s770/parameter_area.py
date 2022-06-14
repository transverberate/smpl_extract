import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
from typing import cast
from typing import List
from construct.core import Adapter
from construct.core import Array
from construct.core import Computed
from construct.core import FixedSized
from construct.core import Int16sl
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import Int8ul
from construct.core import Padding
from construct.core import Struct
from construct.core import Bytes
import numpy as np

from .data_types import MAX_NUM_PARTIAL
from .data_types import MAX_NUM_PATCH
from .data_types import MAX_NUM_PERFORMANCE
from .data_types import MAX_NUM_SAMPLE
from .data_types import MAX_NUM_VOLUME
from .data_types import PARTIAL_PARAMETER_AREA_SIZE
from .data_types import PATCH_PARAMETER_AREA_SIZE
from .data_types import PERFORMANCE_PARAMETER_AREA_SIZE
from .data_types import SAMPLE_PARAMETER_AREA_SIZE
from .data_types import VOLUME_PARAMETER_AREA_SIZE


VolumeParamEntryStruct = Struct(
    "name_raw" / Bytes(16),
    "name" / Computed(lambda this: ""),
    "index" / Computed(lambda this: this._index),
    Padding(16),
    "performance_ptrs" / Array(64, Int16sl),
    Padding(0x60)
)
@dataclass
class VolumeParamEntryContainer:
    name_raw: bytes
    name: str
    index: int
    performance_ptrs: List[int]


class VolumeParamEntryAdapter(Adapter):


    def _decode(self, obj, context, path) -> VolumeParamEntryContainer:
        del context, path  # unused

        container = cast(VolumeParamEntryContainer, obj)
        ptrs_filtered = [x for x in container.performance_ptrs if x >= 0]
        ptrs_filtered = np.unique(np.asarray(ptrs_filtered)).tolist()
        container.performance_ptrs = ptrs_filtered
        return container


    def _encode(self, obj, context, path):
        raise NotImplementedError


VolumeParamEntry = VolumeParamEntryAdapter(VolumeParamEntryStruct)


class VolumeParamEntryList(Adapter):


    def _decode(self, obj, context, path) -> List[VolumeParamEntryContainer]:
        del context, path  # unused

        entries = cast(List[VolumeParamEntryContainer], obj)
        entries_filtered = []
        for entry in entries:
            try:
                entry.name = entry.name_raw.decode(encoding="ascii")
            except UnicodeDecodeError:
                continue
            disqualifiers = (
                len(entry.name) <= 0,
                len(entry.performance_ptrs) <= 0
            )
            if any(disqualifiers):
                continue
            entries_filtered.append(entry)

        return entries_filtered


    def _encode(self, obj, context, path):
        raise NotImplementedError


PerformanceParamEntryStruct = Struct(
    "name_raw" / Bytes(16),
    "name" / Computed(lambda this: ""),
    "index" / Computed(lambda this: this._index),
    "parts_patch_selection" / Array(32, Int8ul),
    "midi_channel_data" / Array(16, Int8ul),
    "parts_level" / Array(32, Int8ul),  #TODO: Breakdown further
    "parts_zone_lower" / Array(32, Int8ul),
    "parts_zone_upper" / Array(32, Int8ul),
    "parts_fade_width_lower" / Array(32, Int8ul),
    "parts_fade_width_upper" / Array(32, Int8ul),
    "parts_program_change" / Int16ul,
    "parts_pitch_bend" / Int16ul,
    "parts_modulation" / Int16ul,
    "parts_hold_pedal" / Int16ul,
    "parts_bend_range" / Int16ul,
    "parts_midi_volume" / Int16ul,
    "parts_after_touch_switch" / Int16ul,
    "parts_after_touch_mode" / Int16ul,
    "velocity_curve_type_data" / Array(16, Int8ul),
    "patch_list" / Array(32, Int16sl),
    Padding(0xC0)
)
@dataclass
class PerformanceParamEntryContainer:
    name_raw: bytes
    name: str
    index: int
    parts_patch_selection: List[int] 
    midi_channel_data: List[int]
    parts_level: List[int]
    parts_zone_lower: List[int]
    parts_zone_upper: List[int]
    parts_program_change: int
    parts_pitch_bend: int
    parts_modulation: int
    parts_hold_pedal: int
    parts_bend_range: int
    parts_midi_volume: int
    parts_after_touch_switch: int
    parts_after_touch_mode: int
    velocity_curve_type_data: List[int]
    patch_list: List[int]


class PerformanceParamEntryAdapter(Adapter):


    def _decode(self, obj, context, path):
        del context, path  # unused
        container = cast(PerformanceParamEntryContainer, obj)
        ptrs_filtered = [x for x in container.patch_list if x >= 0]
        filtered_patches = np.unique(np.asarray(ptrs_filtered)).tolist()
        container.patch_list = filtered_patches
        return container


    def _encode(self, obj, context, path):
        raise NotImplementedError


PerformanceParamEntry = PerformanceParamEntryAdapter(PerformanceParamEntryStruct)


class PerformanceParamEntryList(Adapter):


    def _decode(self, obj, context, path) -> List[PerformanceParamEntryContainer]:
        del context, path  # unused

        entries = cast(List[PerformanceParamEntryContainer], obj)
        entries_filtered = []
        for entry in entries:
            try:
                entry.name = entry.name_raw.decode(encoding="ascii")
            except UnicodeDecodeError:
                continue
            disqualifiers = (
                len(entry.name) <= 0,
                len(entry.patch_list) <= 0
            )
            if any(disqualifiers):
                continue
            entries_filtered.append(entry)

        return entries_filtered


    def _encode(self, obj, context, path):
        raise NotImplementedError


BenderParamStruct = Struct(
    "pitch_ctrl_up" / Int8ul,
    "pitch_ctrl_down" / Int8ul,
    "tva_ctrl" / Int8ul,
    "tvf_ctrl" / Int8ul
)
@dataclass
class BenderParamContainer:
    pitch_ctrl_up: int
    pitch_ctrl_down: int
    tva_ctrl: int
    tvf_ctrl: int


AfterTouchParamStruct = Struct(
    "pitch_ctrl" / Int8ul,
    "tva_ctrl" / Int8ul,
    "tvf_ctrl" / Int8ul,
    "lfo_rate_ctrl" / Int8ul,
    "lfo_pitch_ctrl" / Int8ul,
    "lfo_tva_depth" / Int8ul,
    "lfo_tvf_depth" / Int8ul
)
@dataclass
class AfterTouchParamContainer:
    pitch_ctrl: int
    tva_ctrl: int
    tvf_ctrl: int
    lfo_rate_ctrl: int
    lfo_pitch_ctrl: int
    lfo_tva_depth: int
    lfo_tvf_depth: int


ModulationParamStruct = Struct(
    "lfo_rate_ctrl" / Int8ul,
    "lfo_pitch_ctrl" / Int8ul,
    "lfo_tva_depth" / Int8ul,
    "lfo_tvf_depth" / Int8ul
)
@dataclass
class ModulationParamContainer:
    lfo_rate_ctrl: int
    lfo_pitch_ctrl: int
    lfo_tva_depth: int
    lfo_tvf_depth: int


ControllerParamStruct = Struct(
    "ctrl_num" / Int8ul,
    "pitch_ctrl" / Int8ul,
    "tva_ctrl" / Int8ul,
    "tvf_ctrl" / Int8ul,
    "lfo_rate_ctrl" / Int8ul,
    "lfo_pitch_ctrl" / Int8ul,
    "lfo_tva_depth" / Int8ul,
    "lfo_tvf_depth" / Int8ul
)
@dataclass
class ControllerParamContainer:
    ctrl_num: int
    pitch_ctrl: int
    tva_ctrl: int
    tvf_ctrl: int
    lfo_rate_ctrl: int
    lfo_pitch_ctrl: int
    lfo_tva_depth: int
    lfo_tvf_depth: int


PatchParamEntryStruct = Struct(
    "name_raw" / Bytes(16),
    "name" / Computed(lambda this: ""),
    "index" / Computed(lambda this: this._index),
    "program_change_num" / Int8ul,
    "stereo_mix_level" / Int8ul,
    "total_pan" / Int8ul,
    "patch_level" / Int8ul,
    "output_assign_8" / Int8ul,
    "priority" / Int8ul,
    "cutoff" / Int8ul,
    "velocity_sensitivity" / Int8ul,
    "octave_shift" / Int8ul,
    "coarse_tune" / Int8ul,
    "fine_tune" / Int8ul,
    "smt_ctrl_selection" / Int8ul,
    "smt_ctrl_sensitivity" / Int8ul,
    "out_assign" / Int8ul,
    "analog_feel" / Int8ul,
    Padding(1),
    "keys_partial_selection" / Array(88, Int8ul),
    Padding(8),
    "keys_assign_type" / Array(88, Int8ul),
    Padding(8),
    "bender" / BenderParamStruct,
    "after_touch" / AfterTouchParamStruct,
    "modulation" / ModulationParamStruct,
    Padding(1),
    "controller" / ControllerParamStruct,
    Padding(8),
    "partial_list" / Array(88, Int16sl),
    Padding(0x50)
)
@dataclass
class PatchParamEntryContainer:
    name_raw: bytes
    name: str
    index: int
    program_change_num: int
    stereo_mix_level: int
    total_pan: int
    patch_level: int
    output_assign_8: int
    priority: int
    cutoff: int
    velocity_sensitivity: int
    octave_shift: int
    coarse_tune: int
    fine_tune: int
    smt_ctrl_selection: int
    smt_ctrl_sensitivity: int
    out_assign: int
    analog_feel: int
    keys_partial_selection: List[int]
    keys_assign_type: List[int]
    bender: BenderParamContainer
    after_touch: AfterTouchParamContainer
    modulation: ModulationParamContainer
    controller: ControllerParamContainer
    partial_list: List[int]


class PatchParamEntryAdapter(Adapter):


    def _decode(self, obj, context, path) -> PatchParamEntryContainer:
        del context, path  # unused
        container = cast(PatchParamEntryContainer, obj)
        ptrs_filtered = [x for x in container.partial_list if x >= 0]
        filtered_partials = np.unique(np.asarray(ptrs_filtered)).tolist()
        container.partial_list = filtered_partials
        return container


    def _encode(self, obj, context, path):
        raise NotImplementedError


PatchParamEntry = PatchParamEntryAdapter(PatchParamEntryStruct)


class PatchParamEntryList(Adapter):


    def _decode(self, obj, context, path) -> List[PatchParamEntryContainer]:
        del context, path  # unused

        entries = cast(List[PatchParamEntryContainer], obj)
        entries_filtered = []
        for entry in entries:
            try:
                entry.name = entry.name_raw.decode(encoding="ascii")
            except UnicodeDecodeError:
                continue
            disqualifiers = (
                len(entry.name) <= 0,
                len(entry.partial_list) <= 0
            )
            if any(disqualifiers):
                continue
            entries_filtered.append(entry)

        return entries_filtered


    def _encode(self, obj, context, path):
        raise NotImplementedError


PartialParamSampleSectionStruct = Struct(
    "sample_selection" / Int16ul,
    "pitch_kf" / Int8ul,
    "sample_level" / Int8ul,
    "pan" / Int8ul,
    "coarse_tune" / Int8ul,
    "fine_tune" / Int8ul,
    "smt_velocity_lower" / Int8ul,
    "smt_fade_with_lower" / Int8ul,
    "smt_velocity_upper" / Int8ul,
    "smt_fade_with_upper" / Int8ul,
)
@dataclass
class PartialParamSampleSectionContainer:
    sample_selection: int
    pitch_kf: int
    sample_level: int
    pan: int
    coarse_tune: int
    fine_tune: int
    smt_velocity_lower: int
    smt_fade_with_lower: int
    smt_velocity_upper: int
    smt_fade_with_upper: int


PartialParamTvfSectionStruct = Struct(
    "filter_mode" / Int8ul,
    "cutoff" / Int8ul,
    "resonance" / Int8ul,
    "velocity_curve_type" / Int8ul,
    "velocity_curve_ratio" / Int8ul,
    "time_velocity_sens" / Int8ul,
    "cutoff_velocity_sens" / Int8ul,
    "levels" / Array(4, Int8ul),
    "times" / Array(4, Int8ul),
    "env_tvf_depth" / Int8ul,
    "env_pitch_depth" / Int8ul,
    "tvf_kf_point" / Int8ul,
    "env_time_kf" / Int8ul,
    "env_depth_kf" / Int8ul,
    "cutoff_kf" / Int8ul,
)
@dataclass
class PartialParamTvfSectionContainer:
    filter_mode: int
    cutoff: int
    resonance: int
    velocity_curve_type: int
    velocity_curve_ratio: int
    time_velocity_sens: int
    cutoff_velocity_sens: int
    levels: List[int]
    times: List[int]
    env_tvf_depth: int
    env_pitch_depth: int
    tvf_kf_point: int
    env_time_kf: int
    env_depth_kf: int
    cutoff_kf: int


PartialParamTvaSectionStruct = Struct(
    "velocity_curve_type" / Int8ul,
    "velocity_curve_ratio" / Int8ul,
    "time_velocity_sensitivity" / Int8ul,
    "levels" / Array(4, Int8ul),
    "times" / Array(4, Int8ul),
    Padding(1),
    "tva_kf_point" / Int8ul,
    "env_time_kf" / Int8ul,
    Padding(1),
    "level_kf" / Int8ul
)
@dataclass
class PartialParamTvaSectionContainer:
    velocity_curve_type: int
    velocity_curve_ratio: int
    time_velocity_sensitivity: int
    levels: List[int]
    times: List[int]
    tva_kf_point: int
    env_time_kf: int
    level_kf: int


PartialParamLfoSectionStruct = Struct(
    "wave_form" / Int8ul,
    "rate" / Int8ul,
    "key_sync" / Int8ul,
    "delay" / Int8ul,
    "delay_kf" / Int8ul,
    "detune" / Int8ul,
    "pitch" / Int8ul,
    "tvf_modulation_depth" / Int8ul,
    "tva_modulation_depth" / Int8ul,
)
@dataclass
class PartialParamLfoSectionContainer:
    wave_form: int
    rate: int
    key_sync: int
    delay: int
    delay_kf: int
    detune: int
    pitch: int
    tvf_modulation_depth: int
    tva_modulation_depth: int


PartialParamEntryStruct = Struct(
    "name_raw" / Bytes(16),
    "name" / Computed(lambda this: ""),
    "index" / Computed(lambda this: this._index),
    "sample_1" / PartialParamSampleSectionStruct,
    Padding(1),
    "output_assign_8" / Int8ul,
    "stereo_mix_level" / Int8ul,
    "partial_level" / Int8ul,
    "output_assign_6" / Int8ul,
    "sample_2" / PartialParamSampleSectionStruct,
    Padding(1),
    "pan" / Int8ul,
    "course_tune" / Int8ul,
    "fine_tune" / Int8ul,
    "breath_cntrl" / Int8ul,
    "sample_3" / PartialParamSampleSectionStruct,
    Padding(5),
    "sample_4" / PartialParamSampleSectionStruct,
    "tvf" / PartialParamTvfSectionStruct,
    "tva" / PartialParamTvaSectionStruct,
    "lfo_generator" / PartialParamLfoSectionStruct,
    Padding(7)
)
@dataclass
class PartialParamEntryContainer:
    name_raw: bytes
    name: str
    index: int
    sample_1: PartialParamSampleSectionContainer
    output_assign_8: int
    stereo_mix_level: int
    partial_level: int
    output_assign_6: int
    sample_2: PartialParamSampleSectionContainer
    pan: int
    course_tune: int
    fine_tune: int
    breath_cntrl: int
    sample_3: PartialParamSampleSectionContainer
    sample_4: PartialParamSampleSectionContainer
    tvf: PartialParamTvfSectionContainer
    tva: PartialParamTvaSectionContainer
    lfo_generator: PartialParamLfoSectionContainer


class PartialParamEntryList(Adapter):


    def _decode(self, obj, context, path) -> List[PartialParamEntryContainer]:
        del context, path  # unused

        entries = cast(List[PartialParamEntryContainer], obj)
        entries_filtered = []
        for entry in entries:
            try:
                entry.name = entry.name_raw.decode(encoding="ascii")
            except UnicodeDecodeError:
                continue
            disqualifiers = (
                len(entry.name) <= 0,
            )
            if any(disqualifiers):
                continue
            entries_filtered.append(entry)

        return entries_filtered


    def _encode(self, obj, context, path):
        raise NotImplementedError


SampleParamLoopPointStruct = Struct(
    "raw_value" / Int32ul,
    "fine" / Computed(lambda this: (this.raw_value & 255)),
    "address" / Computed(lambda this: (this.raw_value >> 8)),
)
@dataclass 
class SampleParamLoopPointContainer:
    raw_value: int 
    fine: int
    address: int


SampleParamEntryStruct = Struct(
    "name_raw" / Bytes(16),
    "name" / Computed(lambda this: ""),
    "index" / Computed(lambda this: this._index),
    "start_sample" / SampleParamLoopPointStruct,
    "sustain_loop_start" / SampleParamLoopPointStruct,
    "sustain_loop_end" / SampleParamLoopPointStruct,
    "release_loop_start" / SampleParamLoopPointStruct,
    "release_loop_end" / SampleParamLoopPointStruct,
    "loop_mode" / Int8ul,
    "sustain_loop_enable" / Int8ul,
    "sustain_loop_tune" / Int8ul,
    "release_loop_tune" / Int8ul,
    "seg_top" / Int16ul,
    "seg_length" / Int16ul,
    "sample_mode" / Int8ul,
    "original_key" / Int8ul,
    Padding(2)
)
@dataclass
class SampleParamEntryContainer:
    name_raw: bytes
    name: str
    index: int
    start_sample: SampleParamLoopPointContainer
    sustain_loop_start: SampleParamLoopPointContainer
    sustain_loop_end: SampleParamLoopPointContainer
    release_loop_start: SampleParamLoopPointContainer
    release_loop_end: SampleParamLoopPointContainer
    loop_mode: int
    sustain_loop_enable: int
    sustain_loop_tune: int
    release_loop_tune: int
    seg_top: int
    seg_length: int
    sample_mode: int
    original_key: int


class SampleParamEntryList(Adapter):


    def _decode(self, obj, context, path) -> List[SampleParamEntryContainer]:
        del context, path  # unused

        entries = cast(List[SampleParamEntryContainer], obj)
        entries_filtered = []
        for entry in entries:
            try:
                entry.name = entry.name_raw.decode(encoding="ascii")
            except UnicodeDecodeError:
                continue
            disqualifiers = (
                len(entry.name) <= 0,
            )
            if any(disqualifiers):
                continue
            entries_filtered.append(entry)

        return entries_filtered


    def _encode(self, obj, context, path):
        raise NotImplementedError


def ParamAreaStruct(
    num_volumes:        int = MAX_NUM_VOLUME,
    num_performances:   int = MAX_NUM_PERFORMANCE,
    num_patches:        int = MAX_NUM_PATCH,
    num_partials:       int = MAX_NUM_PARTIAL,
    num_samples:        int = MAX_NUM_SAMPLE
):
    result = Struct(
        "volume_params"        /\
            FixedSized(
                VOLUME_PARAMETER_AREA_SIZE, 
                VolumeParamEntryList(
                    VolumeParamEntry[num_volumes]
                )
            ),
        "performance_params"   /\
            FixedSized(
                PERFORMANCE_PARAMETER_AREA_SIZE,
                PerformanceParamEntryList(
                    PerformanceParamEntry[num_performances]
                )
            ),
        "patch_params"         /\
            FixedSized(
                PATCH_PARAMETER_AREA_SIZE, 
                PatchParamEntryList(
                    PatchParamEntry[num_patches]
                )
            ),
        "partial_params"       /\
            FixedSized(
                PARTIAL_PARAMETER_AREA_SIZE, 
                PartialParamEntryList(
                    PartialParamEntryStruct[num_partials]
                )
            ),
        "sample_params"        /\
            FixedSized(
                SAMPLE_PARAMETER_AREA_SIZE, 
                SampleParamEntryList(
                    SampleParamEntryStruct[num_samples]
                )
            )
    )
    return result
@dataclass
class ParamAreaContainer:
    volume_params:      List[VolumeParamEntryContainer]
    performance_params: List[PerformanceParamEntryContainer]
    patch_params:       List[PatchParamEntryContainer]
    partial_params:     List[PartialParamEntryContainer]
    sample_params:      List[SampleParamEntryContainer]

