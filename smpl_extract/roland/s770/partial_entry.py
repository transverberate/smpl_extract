import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from dataclasses import field
from construct.core import Array
from construct.core import Computed
from construct.core import Construct
from construct.core import ConstructError
from construct.core import ExprValidator
from construct.core import Int16sl
from construct.core import Int8sl
from construct.core import Int8ul
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Pass
from construct.core import Pointer
from construct.core import Struct
from construct.core import Subconstruct
from construct.lib.containers import ListContainer
from typing import cast
from typing import ClassVar
from typing import List
from typing import Optional

from base import Element
from base import ElementTypes
from elements import Traversable
from .data_types import MAX_NUM_PARTIAL
from .data_types import PARTIAL_DIRECTORY_AREA_OFFSET
from .data_types import PARTIAL_DIRECTORY_ENTRY_SIZE
from .data_types import PARTIAL_PARAMETER_AREA_OFFSET
from .data_types import PARTIAL_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .sample_entry import SampleEntryAdapter
from .sample_entry import SampleEntryContainer
from .sample_entry import SampleEntryConstruct
from util.constructs import pass_expression_deeper
from util.constructs import UnsizedConstruct


PartialParamSampleSectionStruct = Struct(
    "sample_selection"      / Int16sl,
    "pitch_kf"              / Int8ul,
    "sample_level"          / Int8ul,
    "pan"                   / Int8sl,
    "coarse_tune"           / Int8sl,
    "fine_tune"             / Int8sl,
    "smt_velocity_lower"    / Int8ul,
    "smt_fade_with_lower"   / Int8ul,
    "smt_velocity_upper"    / Int8ul,
    "smt_fade_with_upper"   / Int8ul,
)
@dataclass
class PartialParamSampleSectionContainer:
    sample_selection:       int
    pitch_kf:               int
    sample_level:           int
    pan:                    int
    coarse_tune:            int
    fine_tune:              int
    smt_velocity_lower:     int
    smt_fade_with_lower:    int
    smt_velocity_upper:     int
    smt_fade_with_upper:    int


PartialParamTvfSectionStruct = Struct(
    "filter_mode"           / Int8ul,
    "cutoff"                / Int8ul,
    "resonance"             / Int8ul,
    "velocity_curve_type"   / Int8ul,
    "velocity_curve_ratio"  / Int8ul,
    "time_velocity_sens"    / Int8ul,
    "cutoff_velocity_sens"  / Int8ul,
    "levels"                / Array(4, Int8ul),
    "times"                 / Array(4, Int8ul),
    "env_tvf_depth"         / Int8ul,
    "env_pitch_depth"       / Int8ul,
    "tvf_kf_point"          / Int8ul,
    "env_time_kf"           / Int8ul,
    "env_depth_kf"          / Int8ul,
    "cutoff_kf"             / Int8ul,
)
@dataclass
class PartialParamTvfSectionContainer:
    filter_mode:            int
    cutoff:                 int
    resonance:              int
    velocity_curve_type:    int
    velocity_curve_ratio:   int
    time_velocity_sens:     int
    cutoff_velocity_sens:   int
    levels:                 List[int]
    times:                  List[int]
    env_tvf_depth:          int
    env_pitch_depth:        int
    tvf_kf_point:           int
    env_time_kf:            int
    env_depth_kf:           int
    cutoff_kf:              int


PartialParamTvaSectionStruct = Struct(
    "velocity_curve_type"       / Int8ul,
    "velocity_curve_ratio"      / Int8ul,
    "time_velocity_sensitivity" / Int8ul,
    "levels"                    / Array(4, Int8ul),
    "times"                     / Array(4, Int8ul),
    Padding(1),
    "tva_kf_point"              / Int8ul,
    "env_time_kf"               / Int8ul,
    Padding(1),
    "level_kf"                  / Int8ul
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
    "wave_form"             / Int8ul,
    "rate"                  / Int8ul,
    "key_sync"              / Int8ul,
    "delay"                 / Int8ul,
    "delay_kf"              / Int8ul,
    "detune"                / Int8ul,
    "pitch"                 / Int8ul,
    "tvf_modulation_depth"  / Int8ul,
    "tva_modulation_depth"  / Int8ul,
)
@dataclass
class PartialParamLfoSectionContainer:
    wave_form:              int
    rate:                   int
    key_sync:               int
    delay:                  int
    delay_kf:               int
    detune:                 int
    pitch:                  int
    tvf_modulation_depth:   int
    tva_modulation_depth:   int


PartialParamEntryStruct = Struct(
    "name"              / PaddedString(16, encoding="ascii"),
    "index"             / Computed(lambda this: this._index),
    "sample_1"          / PartialParamSampleSectionStruct,
    Padding(1),
    "output_assign_8"   / Int8ul,
    "stereo_mix_level"  / Int8ul,
    "partial_level"     / Int8ul,
    "output_assign_6"   / Int8ul,
    "sample_2"          / PartialParamSampleSectionStruct,
    Padding(1),
    "pan"               / Int8ul,
    "course_tune"       / Int8sl,
    "fine_tune"         / Int8sl,
    "breath_cntrl"      / Int8ul,
    "sample_3"          / PartialParamSampleSectionStruct,
    Padding(5),
    "sample_4"          / PartialParamSampleSectionStruct,
    "tvf"               / PartialParamTvfSectionStruct,
    "tva"               / PartialParamTvaSectionStruct,
    "lfo_generator"     / PartialParamLfoSectionStruct,
    Padding(7)
)
@dataclass
class PartialParamEntryContainer:
    name:               str
    index:              int
    sample_1:           PartialParamSampleSectionContainer
    output_assign_8:    int
    stereo_mix_level:   int
    partial_level:      int
    output_assign_6:    int
    sample_2:           PartialParamSampleSectionContainer
    pan:                int
    course_tune:        int
    fine_tune:          int
    breath_cntrl:       int
    sample_3:           PartialParamSampleSectionContainer
    sample_4:           PartialParamSampleSectionContainer
    tvf:                PartialParamTvfSectionContainer
    tva:                PartialParamTvaSectionContainer
    lfo_generator:      PartialParamLfoSectionContainer


def PartialEntryConstruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0<= obj < MAX_NUM_PARTIAL
        ),
        "index"     / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (PARTIAL_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + PARTIAL_DIRECTORY_AREA_OFFSET,
            DirectoryEntryParser
        ),
        "parameter" / Pointer(
            lambda this: \
                (PARTIAL_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + PARTIAL_PARAMETER_AREA_OFFSET,
            PartialParamEntryStruct
        )
    ))
    return result
@dataclass
class PartialEntryContainer:
    index:      int
    directory:  DirectoryEntryContainer
    parameter:  PartialParamEntryContainer


@dataclass
class SampleEntryReference:
    sample_entry:           SampleEntryContainer
    pitch_kf:               int
    sample_level:           int
    pan:                    int
    coarse_tune:            int
    fine_tune:              int
    smt_velocity_lower:     int
    smt_fade_with_lower:    int
    smt_velocity_upper:     int
    smt_fade_with_upper:    int


class SampleEntryReferenceAdapter(Subconstruct):


    def _parse(self, stream, context, path) -> SampleEntryReference:
        container = cast(
            PartialParamSampleSectionContainer, 
            context["ref_container"]
        )
        if container.sample_selection < 0:
            raise ConstructError
        sample_entry_sc = SampleEntryAdapter(
            SampleEntryConstruct(container.sample_selection)
        )
        new_path = path + " -> sample_entries"
        sample_entry = sample_entry_sc._parse(  # type: ignore
            stream, 
            context, 
            new_path
        )  
        result = SampleEntryReference(
            sample_entry=sample_entry,
            pitch_kf=container.pitch_kf,
            sample_level=container.sample_level,
            pan=container.pan,
            coarse_tune=container.coarse_tune,
            fine_tune=container.fine_tune,
            smt_velocity_lower=container.smt_velocity_lower,
            smt_velocity_upper=container.smt_velocity_upper,
            smt_fade_with_lower=container.smt_fade_with_lower,
            smt_fade_with_upper=container.smt_fade_with_upper
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError


@dataclass
class PartialEntry(Traversable):
    directory_name:             str
    parameter_name:             str
    sample_entry_references:    List[SampleEntryReference]

    _parent:    Optional[Element]       = None
    _path:      List[str]               = field(default_factory=list)

    type_id:    ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:  ClassVar[str]           = "Roland S-770 Partial"


    def __post_init__(self):
        self._sample_entries = None


    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def sample_entries(self):
        if not self._sample_entries:
            self._sample_entries = [
                x.sample_entry for x in self.sample_entry_references
            ]
        return self._sample_entries


    @property
    def children(self):
        result = self.sample_entries
        return result


class PartialEntryAdapter(Subconstruct):


    def _parse(self, stream, context, path) -> PartialEntry:
        sc = self.subcon
        container = cast(
            PartialEntryContainer, 
            sc._parse(stream, context, path)  # type: ignore
        )
        sample_ref_containers = ListContainer([
            container.parameter.sample_1,
            container.parameter.sample_2,
            container.parameter.sample_3,
            container.parameter.sample_4
        ])

        sample_references = []
        parser = SampleEntryReferenceAdapter(Pass)
        for ref_container in sample_ref_containers:
            ctx = context.copy()
            ctx["ref_container"] = ref_container
            try:
                sample_reference = parser._parse(stream, ctx, path)  # type: ignore
            except (ConstructError, UnicodeDecodeError) as e:
                continue
            sample_references.append(sample_reference)

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys():
            if "parent" in context._.keys():
                parent = cast(Element, context._.parent)
                element_path = parent.path
            if "fat" in context._.keys():
                context["fat"] = context._.fat

        name = container.directory.name
        partial_path = element_path + [name]

        partial = PartialEntry(
            container.directory.name,
            container.parameter.name,
            sample_references,
            parent,
            partial_path
        )
        context["parent"] = partial
        try:
            dir_version = context["_"]["_dir_version"]
            context["_dir_version"] = dir_version
        except KeyError as e:
            pass
        
        return partial


    def _encode(self, obj, context, path):
        raise NotImplementedError

