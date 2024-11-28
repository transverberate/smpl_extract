from dataclasses import dataclass
from dataclasses import field
from construct.core import Adapter
from construct.core import Array
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import Int16sl
from construct.core import Int8ul
from construct.core import Lazy
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Pointer
from construct.core import Struct
import numpy as np
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import cast

from smpl_extract.base import Element
from smpl_extract.base import ElementTypes
from smpl_extract.structural import T_ROUTINE
from smpl_extract.structural import Traversable
from smpl_extract.util.constructs import ChildInfo
from smpl_extract.util.constructs import ElementAdapter
from smpl_extract.util.constructs import pass_expression_deeper
from smpl_extract.util.constructs import SafeListConstruct
from smpl_extract.util.constructs import UnsizedConstruct
from smpl_extract.util.dataclass import get_common_field_args

from .data_types import MAX_NUM_PATCH
from .data_types import NUM_KEYS
from .data_types import PATCH_DIRECTORY_AREA_OFFSET
from .data_types import PATCH_DIRECTORY_ENTRY_SIZE
from .data_types import PATCH_PARAMETER_AREA_OFFSET
from .data_types import PATCH_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .partial_entry import PartialEntry
from .partial_entry import PartialEntryAdapter
from .partial_entry import PartialEntryConstruct


BenderParamStruct = Struct(
    "pitch_ctrl_up"     / Int8ul,
    "pitch_ctrl_down"   / Int8ul,
    "tva_ctrl"          / Int8ul,
    "tvf_ctrl"          / Int8ul
)
@dataclass
class BenderParamContainer:
    pitch_ctrl_up:      int = 0
    pitch_ctrl_down:    int = 0
    tva_ctrl:           int = 0
    tvf_ctrl:           int = 0


AfterTouchParamStruct = Struct(
    "pitch_ctrl"        / Int8ul,
    "tva_ctrl"          / Int8ul,
    "tvf_ctrl"          / Int8ul,
    "lfo_rate_ctrl"     / Int8ul,
    "lfo_pitch_ctrl"    / Int8ul,
    "lfo_tva_depth"     / Int8ul,
    "lfo_tvf_depth"     / Int8ul
)
@dataclass
class AfterTouchParamContainer:
    pitch_ctrl:     int = 0
    tva_ctrl:       int = 0
    tvf_ctrl:       int = 0
    lfo_rate_ctrl:  int = 0
    lfo_pitch_ctrl: int = 0
    lfo_tva_depth:  int = 0
    lfo_tvf_depth:  int = 0


ModulationParamStruct = Struct(
    "lfo_rate_ctrl"     / Int8ul,
    "lfo_pitch_ctrl"    / Int8ul,
    "lfo_tva_depth"     / Int8ul,
    "lfo_tvf_depth"     / Int8ul
)
@dataclass
class ModulationParamContainer:
    lfo_rate_ctrl:  int = 0
    lfo_pitch_ctrl: int = 0
    lfo_tva_depth:  int = 0
    lfo_tvf_depth:  int = 0


ControllerParamStruct = Struct(
    "ctrl_num"          / Int8ul,
    "pitch_ctrl"        / Int8ul,
    "tva_ctrl"          / Int8ul,
    "tvf_ctrl"          / Int8ul,
    "lfo_rate_ctrl"     / Int8ul,
    "lfo_pitch_ctrl"    / Int8ul,
    "lfo_tva_depth"     / Int8ul,
    "lfo_tvf_depth"     / Int8ul
)
@dataclass
class ControllerParamContainer:
    ctrl_num:       int = 0
    pitch_ctrl:     int = 0
    tva_ctrl:       int = 0
    tvf_ctrl:       int = 0
    lfo_rate_ctrl:  int = 0
    lfo_pitch_ctrl: int = 0
    lfo_tva_depth:  int = 0
    lfo_tvf_depth:  int = 0


@dataclass
class PatchParamEntryCommon:
    program_change_num:     int = 0
    stereo_mix_level:       int = 0
    total_pan:              int = 0
    patch_level:            int = 0
    output_assign_8:        int = 0
    priority:               int = 0
    cutoff:                 int = 0
    velocity_sensitivity:   int = 0
    octave_shift:           int = 0
    coarse_tune:            int = 0
    fine_tune:              int = 0
    smt_ctrl_selection:     int = 0
    smt_ctrl_sensitivity:   int = 0
    out_assign:             int = 0
    analog_feel:            int = 0

    keys_partial_selection: List[int] = \
        field(default_factory=list)
    keys_assign_type: List[int] = \
        field(default_factory=list)
    bender: BenderParamContainer = \
        field(default_factory=BenderParamContainer)
    after_touch: AfterTouchParamContainer = \
        field(default_factory=AfterTouchParamContainer)
    modulation: ModulationParamContainer = \
        field(default_factory=ModulationParamContainer)
    controller: ControllerParamContainer = \
        field(default_factory=ControllerParamContainer)


PatchParamEntryStruct = Struct(
    "name"                      / PaddedString(16, encoding="ascii"),
    "index"                     / Computed(lambda this: this._index),
    "program_change_num"        / Int8ul,
    "stereo_mix_level"          / Int8ul,
    "total_pan"                 / Int8ul,
    "patch_level"               / Int8ul,
    "output_assign_8"           / Int8ul,
    "priority"                  / Int8ul,
    "cutoff"                    / Int8ul,
    "velocity_sensitivity"      / Int8ul,
    "octave_shift"              / Int8ul,
    "coarse_tune"               / Int8ul,
    "fine_tune"                 / Int8ul,
    "smt_ctrl_selection"        / Int8ul,
    "smt_ctrl_sensitivity"      / Int8ul,
    "out_assign"                / Int8ul,
    "analog_feel"               / Int8ul,
    Padding(1),
    "keys_partial_selection"    / Array(NUM_KEYS, Int8ul),
    Padding(8),
    "keys_assign_type"          / Array(NUM_KEYS, Int8ul),
    Padding(8),
    "bender"                    / BenderParamStruct,
    "after_touch"               / AfterTouchParamStruct,
    "modulation"                / ModulationParamStruct,
    Padding(1),
    "controller"                / ControllerParamStruct,
    Padding(8),
    "partial_list"              / Array(NUM_KEYS, Int16sl),
    Padding(0x50)
)
@dataclass
class PatchParamEntryContainer(PatchParamEntryCommon):
    name:                   str         = ""
    index:                  int         = 0
    partial_list:           List[int]   = field(default_factory=list)


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


PatchParamEntryParser = PatchParamEntryAdapter(PatchParamEntryStruct)


def PatchEntryConstruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0 <= obj < MAX_NUM_PATCH
        ),
        "index"     / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (PATCH_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + PATCH_DIRECTORY_AREA_OFFSET,
            DirectoryEntryParser
        ),
        "parameter" / Pointer(
            lambda this: \
                (PATCH_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + PATCH_PARAMETER_AREA_OFFSET,
            PatchParamEntryParser
        ),
        "partial_entries" / Lazy(SafeListConstruct(
            lambda this: len(this.parameter.partial_list),
            PartialEntryAdapter(PartialEntryConstruct(lambda this: 
                this.parameter.partial_list[this._index]
            ))
        ))
    ))
    return result
@dataclass
class PatchEntryContainer:
    index:              int
    directory:          DirectoryEntryContainer
    parameter:          PatchParamEntryContainer
    partial_entries:    Callable


@dataclass
class PatchEntry(PatchParamEntryCommon, Traversable):
    directory_name:         str                     = ""
    parameter_name:         str                     = ""
    _f_realize_children:    Callable                = lambda x: None
    _parent:                Optional[Element]       = None
    _path:                  List[str]               = field(default_factory=list)
    _routines:              Dict[str, T_ROUTINE]    = field(default_factory=dict)

    _children:              Optional[List[Element]] = None

    type_id:                ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:              ClassVar[str]           = "Roland S-7xx Patch"


    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def partial_entries(self) -> List[PartialEntry]:
        result = self.children
        return result  # type: ignore


class PatchEntryAdapter(ElementAdapter):


    def _decode_element(
            self, 
            obj, 
            child_info: ChildInfo, 
            context: Dict[str, Any], 
            path: str
        ):
        del path  # unused
        
        container = cast(PatchEntryContainer, obj)

        parent = child_info.parent
        parent_path = child_info.parent_path

        name = container.directory.name
        patch_path = parent_path + [name]

        try:
            fat = context["_"]["fat"]
            context["fat"] = fat
        except KeyError as e:
            pass

        common_args = get_common_field_args(
            PatchParamEntryCommon, 
            container.parameter
        )

        patch = PatchEntry(
            **common_args,
            directory_name=container.directory.name,
            parameter_name=container.parameter.name,
            _f_realize_children=self.wrap_child_realization(
                container.partial_entries,
                context
            ),
            _parent=parent,
            _path=patch_path,
            _routines=child_info.routines
        )
        try:
            dir_version = context["_"]["_dir_version"]
            context["_dir_version"] = dir_version
        except KeyError as e:
            pass
        
        return patch


    def _encode(self, obj, context, path):
        raise NotImplementedError

