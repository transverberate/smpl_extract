import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from dataclasses import field
from construct.core import Adapter
from construct.core import Array
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import Int8ul
from construct.core import Int16sl
from construct.core import Int16ul
from construct.core import Lazy
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Pass
from construct.core import Pointer
from construct.core import Struct
from construct.lib.containers import Container
import numpy as np
from typing import Callable
from typing import ClassVar
from typing import List
from typing import cast
from typing import Optional

from base import Element
from base import ElementTypes
from elements import Traversable
from .data_types import MAX_NUM_PERFORMANCE
from .data_types import PERFORMANCE_DIRECTORY_AREA_OFFSET
from .data_types import PERFORMANCE_DIRECTORY_ENTRY_SIZE
from .data_types import PERFORMANCE_PARAMETER_AREA_OFFSET
from .data_types import PERFORMANCE_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .patch_entry import PatchEntryAdapter
from .patch_entry import PatchEntryConstruct
from .program_file import ProgramFileAdapter
from .sample_file import SampleFileListAdapter
from util.constructs import pass_expression_deeper
from util.constructs import SafeListConstruct
from util.constructs import UnsizedConstruct
from util.dataclass import get_common_field_args


@dataclass
class PerformanceParamCommon:
    parts_patch_selection:      List[int]   = field(default_factory=list)
    midi_channel_data:          List[int]   = field(default_factory=list)
    parts_level:                List[int]   = field(default_factory=list)
    parts_zone_lower:           List[int]   = field(default_factory=list)
    parts_zone_upper:           List[int]   = field(default_factory=list)
    parts_program_change:       int         = 0
    parts_pitch_bend:           int         = 0
    parts_modulation:           int         = 0
    parts_hold_pedal:           int         = 0
    parts_bend_range:           int         = 0
    parts_midi_volume:          int         = 0
    parts_after_touch_switch:   int         = 0
    parts_after_touch_mode:     int         = 0
    velocity_curve_type_data:   List[int]   = field(default_factory=list)


PerformanceParamEntryStruct = Struct(
    "name"                      / PaddedString(16, encoding="ascii"),
    "index"                     / Computed(lambda this: this._index),
    "parts_patch_selection"     / Array(32, Int8ul),
    "midi_channel_data"         / Array(16, Int8ul),
    "parts_level"               / Array(32, Int8ul),  #TODO: Breakdown further
    "parts_zone_lower"          / Array(32, Int8ul),
    "parts_zone_upper"          / Array(32, Int8ul),
    "parts_fade_width_lower"    / Array(32, Int8ul),
    "parts_fade_width_upper"    / Array(32, Int8ul),
    "parts_program_change"      / Int16ul,
    "parts_pitch_bend"          / Int16ul,
    "parts_modulation"          / Int16ul,
    "parts_hold_pedal"          / Int16ul,
    "parts_bend_range"          / Int16ul,
    "parts_midi_volume"         / Int16ul,
    "parts_after_touch_switch"  / Int16ul,
    "parts_after_touch_mode"    / Int16ul,
    "velocity_curve_type_data"  / Array(16, Int8ul),
    "patch_list"                / Array(32, Int16sl),
    Padding(0xC0)
)
@dataclass
class PerformanceParamEntryContainer(PerformanceParamCommon):
    name:                       str         = ""
    index:                      int         = 0
    patch_list:                 List[int]   = field(default_factory=list)


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


PerformanceParamEntryParser = PerformanceParamEntryAdapter(PerformanceParamEntryStruct)


def PerformanceEntryConstruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0 <= obj < MAX_NUM_PERFORMANCE
        ),
        "index"     / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (PERFORMANCE_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + PERFORMANCE_DIRECTORY_AREA_OFFSET,
            DirectoryEntryParser
        ),
        "parameter" / Pointer(
            lambda this: \
                (PERFORMANCE_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + PERFORMANCE_PARAMETER_AREA_OFFSET,
            PerformanceParamEntryParser
        ),
        "patch_entries" / Lazy(SafeListConstruct(
            lambda this: len(this.parameter.patch_list),
            PatchEntryAdapter(PatchEntryConstruct(lambda this: 
                this.parameter.patch_list[this._index]
            ))
        ))
    ))
    return result
@dataclass
class PerformanceEntryContainer:
    index:          int
    directory:      DirectoryEntryContainer
    parameter:      PerformanceParamEntryContainer
    patch_entries:  Callable


@dataclass
class PerformanceEntry(PerformanceParamCommon, Traversable):
    directory_name:     str                     = ""
    parameter_name:     str                     = ""
    _f_patch_entries:   Callable                = lambda x: None
    _parent:            Optional[Element]       = None
    _path:              List[str]               = field(default_factory=list)

    type_id:            ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:          ClassVar[str]           = "Roland S-770 Performance"


    def __post_init__(self):
        self._patch_entries = None
        self._files = None


    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def patch_entries(self):
        if not self._patch_entries:
            self._patch_entries = self._f_patch_entries()
        return self._patch_entries


    @property
    def files(self):
        if self._files is None:
            sc_program = ProgramFileAdapter(Pass)
            sc_samples = SampleFileListAdapter(Pass)
            patches = list(self.patch_entries.values())
            context = Container(_=Container(parent=self))
            path = ""

            programs = []
            samples = []
            for patch in patches:
                program = sc_program._decode(
                    patch,
                    context,  # type: ignore
                    path
                )

                samples_result = sc_samples._decode(
                    patch,
                    context,  # type: ignore
                    path
                )

                programs.append(program)
                samples += samples_result
            
            files = programs + samples
            self._files = files

        return self._files


    @property
    def children(self):
        result = self.files
        return result


class PerformanceEntryAdapter(Adapter):


    def _decode(self, obj, context, path) -> PerformanceEntry:
        container = cast(PerformanceEntryContainer, obj)

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys():
            if "parent" in context._.keys():
                parent = cast(Element, context._.parent)
                element_path = parent.path
            if "fat" in context._.keys():
                context["fat"] = context._.fat

        name = container.directory.name
        performance_path = element_path + [name]

        common_args = get_common_field_args(
            PerformanceParamCommon, 
            container.parameter
        )

        performance = PerformanceEntry(
            **common_args,
            directory_name=container.directory.name,
            parameter_name=container.parameter.name,
            _f_patch_entries=container.patch_entries,
            _parent=parent,
            _path=performance_path
        )
        context["parent"] = performance
        try:
            dir_version = context["_"]["_dir_version"]
            context["_dir_version"] = dir_version
        except KeyError as e:
            pass
        
        return performance


    def _encode(self, obj, context, path):
        raise NotImplementedError

