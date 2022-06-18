import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from dataclasses import field
from construct.core import Adapter
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import Lazy
from construct.core import Pointer
from construct.core import Struct
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
from .directory_area import DirectoryEntryStruct
from .parameter_area import PerformanceParamEntry
from .parameter_area import PerformanceParamEntryContainer
from .patch_entry import PatchEntryAdapter
from .patch_entry import PatchEntryStruct
from util.constructs import pass_expression_deeper
from util.constructs import SafeListConstruct
from util.constructs import UnsizedConstruct


def PerformanceEntryStruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0 <= obj < MAX_NUM_PERFORMANCE
        ),
        "index" / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (PERFORMANCE_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + PERFORMANCE_DIRECTORY_AREA_OFFSET,
            DirectoryEntryStruct
        ),
        "parameter" / Pointer(
            lambda this: \
                (PERFORMANCE_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + PERFORMANCE_PARAMETER_AREA_OFFSET,
            PerformanceParamEntry
        ),
        "patch_entries" / Lazy(SafeListConstruct(
            lambda this: len(this.parameter.patch_list),
            PatchEntryAdapter(PatchEntryStruct(lambda this: 
                this.parameter.patch_list[this._index]
            ))
        ))
    ))
    return result
@dataclass
class PerformanceEntryContainer:
    index: int
    directory: DirectoryEntryContainer
    parameter: PerformanceParamEntryContainer
    patch_entries: Callable


@dataclass
class PerformanceEntry(Traversable):
    directory_name: str
    parameter_name: str
    _f_patch_entries: Callable
    _parent: Optional[Element] = None
    _path: List[str] = field(default_factory=list)

    type_id: ClassVar[ElementTypes] = ElementTypes.DirectoryEntry
    type_name: ClassVar[str] = "Roland S-770 Performance"


    def __post_init__(self):
        self._patch_entries = None


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
    def children(self):
        result = list(self.patch_entries.values())
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

        performance = PerformanceEntry(
            container.directory.name,
            container.parameter.name,
            container.patch_entries,
            parent,
            performance_path
        )
        context["parent"] = performance
        
        return performance


    def _encode(self, obj, context, path):
        raise NotImplementedError

