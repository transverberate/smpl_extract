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
from typing import Dict
from typing import cast
from typing import ClassVar
from typing import List
from typing import Optional

from smpl_extract.base import Element
from smpl_extract.base import ElementTypes
from smpl_extract.structural import T_ROUTINE
from smpl_extract.structural import Traversable
from smpl_extract.util.constructs import pass_expression_deeper
from smpl_extract.util.constructs import pull_child_info
from smpl_extract.util.constructs import UnsizedConstruct
from smpl_extract.util.dataclass import get_common_field_args

from .data_types import MAX_NUM_PARTIAL
from .data_types import PARTIAL_DIRECTORY_AREA_OFFSET
from .data_types import PARTIAL_DIRECTORY_ENTRY_SIZE
from .data_types import PARTIAL_PARAMETER_AREA_OFFSET
from .data_types import PARTIAL_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .sample_entry import SampleEntry
from .sample_entry import SampleEntryAdapter
from .sample_entry import SampleEntryConstruct


@dataclass
class PartialParamSampleSectionCommon:
    pitch_kf:               int = 0
    sample_level:           int = 0
    pan:                    int = 0
    coarse_tune:            int = 0
    fine_tune:              int = 0
    smt_velocity_lower:     int = 0
    smt_fade_with_lower:    int = 0
    smt_velocity_upper:     int = 0
    smt_fade_with_upper:    int = 0


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
class PartialParamSampleSectionContainer(PartialParamSampleSectionCommon):
    sample_selection:       int = 0


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
    filter_mode:            int         = 0
    cutoff:                 int         = 0
    resonance:              int         = 0
    velocity_curve_type:    int         = 0
    velocity_curve_ratio:   int         = 0
    time_velocity_sens:     int         = 0
    cutoff_velocity_sens:   int         = 0
    levels:                 List[int]   = field(default_factory=list)
    times:                  List[int]   = field(default_factory=list)
    env_tvf_depth:          int         = 0
    env_pitch_depth:        int         = 0
    tvf_kf_point:           int         = 0
    env_time_kf:            int         = 0
    env_depth_kf:           int         = 0
    cutoff_kf:              int         = 0


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
    velocity_curve_type:        int         = 0
    velocity_curve_ratio:       int         = 0
    time_velocity_sensitivity:  int         = 0
    levels:                     List[int]   = field(default_factory=list)
    times:                      List[int]   = field(default_factory=list)
    tva_kf_point:               int         = 0
    env_time_kf:                int         = 0
    level_kf:                   int         = 0


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
    wave_form:              int = 0
    rate:                   int = 0
    key_sync:               int = 0
    delay:                  int = 0
    delay_kf:               int = 0
    detune:                 int = 0
    pitch:                  int = 0
    tvf_modulation_depth:   int = 0
    tva_modulation_depth:   int = 0


@dataclass
class PartialParamCommon:
    output_assign_8:    int = 0
    stereo_mix_level:   int = 0
    partial_level:      int = 0
    output_assign_6:    int = 0
    pan:                int = 0
    course_tune:        int = 0
    fine_tune:          int = 0
    breath_cntrl:       int = 0

    tvf: PartialParamTvfSectionContainer = \
        field(default_factory=PartialParamTvfSectionContainer)
    tva: PartialParamTvaSectionContainer = \
        field(default_factory=PartialParamTvaSectionContainer)
    lfo_generator: PartialParamLfoSectionContainer = \
        field(default_factory=PartialParamLfoSectionContainer)


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
class PartialParamEntryContainer(PartialParamCommon):
    name:       str = ""
    index:      int = 0

    sample_1: PartialParamSampleSectionContainer = \
        field(default_factory=PartialParamSampleSectionContainer)
    sample_2: PartialParamSampleSectionContainer = \
        field(default_factory=PartialParamSampleSectionContainer)
    sample_3: PartialParamSampleSectionContainer = \
        field(default_factory=PartialParamSampleSectionContainer)
    sample_4: PartialParamSampleSectionContainer = \
        field(default_factory=PartialParamSampleSectionContainer)


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
class SampleEntryReference(PartialParamSampleSectionCommon):
    sample_entry: SampleEntry = field(default_factory=SampleEntry)


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
class PartialEntry(PartialParamCommon, Traversable[SampleEntry]):
    directory_name: str = ""
    parameter_name: str = ""

    sample_entry_references: List[SampleEntryReference] = \
        field(default_factory=list)

    _parent:                Optional[Element]       = None
    _path:                  List[str]               = field(default_factory=list)
    _routines:              Dict[str, T_ROUTINE]    = field(default_factory=dict)

    type_id:                ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:              ClassVar[str]           = "Roland S-7xx Partial"


    def __post_init__(self):
        self._sample_entries = None


    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def sample_entries(self) -> List[SampleEntry]:
        if not self._sample_entries:
            sample_entries = []
            path = self.path
            for reference in self.sample_entry_references:
                sample_entry = reference.sample_entry
                new_path = path + [sample_entry.path[-1]]
                sample_entry._parent = self
                sample_entry._path = new_path
                sample_entries.append(sample_entry)
            
            for routine in self._routines.values():
                sample_entries = routine(sample_entries)
            self._sample_entries = sample_entries
        return self._sample_entries  # type: ignore


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

        name = container.directory.name
        child_info = pull_child_info(context, name)
        parent = child_info.parent

        common_args = get_common_field_args(
            PartialParamCommon, 
            container.parameter
        )

        partial = PartialEntry(
            **common_args,
            directory_name=container.directory.name,
            parameter_name=container.parameter.name,
            sample_entry_references=sample_references,
            _parent=parent,
            _path=child_info.next_path,
            _routines=child_info.routines
        )
        try:
            dir_version = context["_"]["_dir_version"]
            context["_dir_version"] = dir_version
        except KeyError as e:
            pass
        
        return partial


    def _encode(self, obj, context, path):
        raise NotImplementedError

