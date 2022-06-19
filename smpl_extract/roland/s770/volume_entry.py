import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from construct.core import Adapter
from construct.core import Array
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import Int16sl
from construct.core import Lazy
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Pointer
from construct.core import Struct
import numpy as np
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import List
from typing import cast

from base import ElementTypes
from elements import Traversable
from .data_types import MAX_NUM_VOLUME
from .data_types import VOLUME_DIRECTORY_AREA_OFFSET
from .data_types import VOLUME_DIRECTORY_ENTRY_SIZE
from .data_types import VOLUME_PARAMETER_AREA_OFFSET
from .data_types import VOLUME_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .performance_entry import PerformanceEntryAdapter
from .performance_entry import PerformanceEntryConstruct
from util.constructs import SafeListConstruct
from util.constructs import UnsizedConstruct
from util.constructs import pass_expression_deeper


VolumeParamEntryStruct = Struct(
    "name"              / PaddedString(16, encoding="ascii"),
    Padding(16),
    "performance_ptrs"  / Array(64, Int16sl),
    Padding(0x60)
)
@dataclass
class VolumeParamEntryContainer:
    name:               str
    index:              int
    performance_ptrs:   List[int]


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


VolumeParamEntryParser = VolumeParamEntryAdapter(VolumeParamEntryStruct)


def VolumeEntryConstruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0 <= obj < MAX_NUM_VOLUME
        ),
        "index"     / Computed(index_expr),
        "directory" / Pointer(
            lambda this: \
                (VOLUME_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + VOLUME_DIRECTORY_AREA_OFFSET,
            DirectoryEntryParser
        ),
        "parameter" / Pointer(
            lambda this: \
                (VOLUME_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + VOLUME_PARAMETER_AREA_OFFSET,
            VolumeParamEntryParser
        ),
        "performance_entries" / Lazy(SafeListConstruct(
            lambda this: len(this.parameter.performance_ptrs),
            PerformanceEntryAdapter(PerformanceEntryConstruct(
                lambda this: this.parameter.performance_ptrs[this._index]
            ))
        ))
    ))
    return result
@dataclass
class VolumeEntryContainer:
    index:                  int
    directory:              DirectoryEntryContainer
    parameter:              VolumeParamEntryContainer
    performance_entries:    Callable


@dataclass
class VolumeEntry(Traversable):
    index:                  int
    directory_name:         str
    parameter_name:         str
    _f_performance_entries: Callable

    type_id:                ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:              ClassVar[str]           = "Roland S-770 Volume"


    def __post_init__(self):
        self._performance_entries = None


    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def performance_entries(self):
        if not self._performance_entries:
            self._performance_entries = self._f_performance_entries()
        return self._performance_entries


    @property
    def children(self):
        result = list(self.performance_entries.values())
        return result


class VolumeEntryAdapter(Adapter):


    def _decode(self, obj, context, path) -> VolumeEntry:
        container = cast(VolumeEntryContainer, obj)
        volume = VolumeEntry(
            container.index,
            container.directory.name,
            container.parameter.name,
            container.performance_entries
        )
        context["parent"] = volume
        return volume


    def _encode(self, obj, context, path):
        raise NotImplementedError


def VolumeEntriesList(num_volumes: Any = MAX_NUM_VOLUME):
    result = SafeListConstruct(
        num_volumes, 
        VolumeEntryAdapter(
            VolumeEntryConstruct(lambda this: this._index)
        )
    )
    return result

