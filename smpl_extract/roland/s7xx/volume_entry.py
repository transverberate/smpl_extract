from dataclasses import dataclass
from construct.core import Adapter
from construct.core import Array
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import evaluate
from construct.core import Int16sl
from construct.core import Lazy
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Pointer
from construct.core import Struct
from construct.core import Subconstruct
import numpy as np
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import List
from typing import cast

from smpl_extract.base import ElementTypes
from smpl_extract.structural import Traversable
from smpl_extract.util.constructs import ElementAdapter
from smpl_extract.util.constructs import pass_expression_deeper
from smpl_extract.util.constructs import SafeListConstruct
from smpl_extract.util.constructs import UnsizedConstruct

from .data_types import PERFORMANCE_DIRECTORY_AREA_OFFSET
from .data_types import MAX_NUM_PERFORMANCE
from .data_types import MAX_NUM_VOLUME
from .data_types import RolandFileType
from .data_types import VOLUME_DIRECTORY_AREA_OFFSET
from .data_types import VOLUME_DIRECTORY_ENTRY_SIZE
from .data_types import VOLUME_PARAMETER_AREA_OFFSET
from .data_types import VOLUME_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryParser
from .performance_entry import PerformanceEntry, PerformanceEntryAdapter
from .performance_entry import PerformanceEntryConstruct


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
class VolumeEntry(Traversable[PerformanceEntry]):
    index:                  int
    directory_name:         str
    parameter_name:         str
    performance_ptrs:       List[int]
    _f_realize_children:    Callable[[Dict[str, Any]], List[PerformanceEntry]]

    type_id:                ClassVar[ElementTypes]  = ElementTypes.DirectoryEntry
    type_name:              ClassVar[str]           = "Roland S-7xx Volume"


    def __post_init__(self):
        self._path = []
        self._parent = None
        self._routines = {}
        self._children = None
        

    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def performance_entries(self):
        result = self.children
        return result


    @property
    def path(self):
        result = [self.name]
        return result


class VolumeEntryAdapter(ElementAdapter):

    def _decode_element(
            self, 
            obj, 
            children_info,
            context: Dict[str, Any], 
            path: str
    ):
        del children_info, path

        container = cast(VolumeEntryContainer, obj)
        volume = VolumeEntry(
            container.index,
            container.directory.name,
            container.parameter.name,
            container.parameter.performance_ptrs,
            _f_realize_children=self.wrap_child_realization(  # type: ignore
                container.performance_entries,
                context
            )
        )

        return volume


    def _encode(self, obj, context, path):
        raise NotImplementedError


class VolumeEntriesList(Subconstruct):


    def __init__(
            self, 
            num_volumes,
            num_performances
    ) -> None:
        super().__init__(SafeListConstruct(
            num_volumes, # type: ignore
            VolumeEntryAdapter(VolumeEntryConstruct(lambda this: this._index))
        ))
        self.num_performances = num_performances


    def _parse_orphan_performances(
            self, 
            volume_entries: List[VolumeEntry],
            volume_performance_ptrs: np.ndarray,
            stream, 
            context, 
            path) -> List[VolumeEntry]:

        # parse the entire performance directory
        performances_construct = Pointer(PERFORMANCE_DIRECTORY_AREA_OFFSET, 
            SafeListConstruct(
                MAX_NUM_PERFORMANCE, 
                DirectoryEntryParser,
            )
        )
        performances = performances_construct._parsereport(stream, context, path)  # type: ignore
        performances = cast(List[DirectoryEntryContainer], performances)
        performances = list(p for p in performances if p.file_type == RolandFileType.PERFORMANCE)
        
        performance_ptrs = np.array(list(p.index for p in performances))
        if np.size(volume_performance_ptrs, 0) > 0:
            mask = np.isin(performance_ptrs, np.array(volume_performance_ptrs), invert=True)
            orphan_ptrs = performance_ptrs[mask].tolist()
        else:
            orphan_ptrs = performance_ptrs.tolist()

        # create a new pseudo-volume containing the orphans
        if len(volume_entries) == 0:
            volume_name = "All Performances" 
        else:
            volume_name = "_Orphan_perf"  # hopefully no name collisions

        constr = UnsizedConstruct(Struct("performance_entries" / Lazy(SafeListConstruct(
            lambda this: len(orphan_ptrs),
            PerformanceEntryAdapter(PerformanceEntryConstruct(
                lambda this: orphan_ptrs[this._index]
            )))
        )))._parsereport(stream, context, path)  # type: ignore
        new_volume = VolumeEntry(
            MAX_NUM_VOLUME,
            volume_name,
            volume_name,
            orphan_ptrs,
            _f_realize_children=ElementAdapter.wrap_child_realization(  # type: ignore
                constr.performance_entries,
                context
            )
        )
        volume_entries.append(new_volume)

        return volume_entries


    def _parse(self, stream, context, path):
        num_performances = evaluate(self.num_performances, context)
        
        volume_entries = cast(
            List[VolumeEntry],
            self.subcon._parsereport(stream, context, path)  # type: ignore
        )
        volume_performance_ptrs = list((entry.performance_ptrs) for entry in volume_entries)
        if len(volume_performance_ptrs) > 0:
            volume_performance_ptrs = np.concatenate(volume_performance_ptrs)
        else:
            volume_performance_ptrs = np.array([])
        volume_performance_ptrs = np.unique(volume_performance_ptrs)

        # Check for the existance of orphan performances
        if np.size(volume_performance_ptrs, 0) < num_performances:
            volume_entries = self._parse_orphan_performances(
                volume_entries, 
                volume_performance_ptrs,
                stream, 
                context, 
                path
            ) 
        
        return volume_entries

