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
from typing import Optional
from typing import cast

from base import Element
from base import ElementTypes
from elements import Traversable
from .data_types import MAX_NUM_PATCH
from .data_types import PATCH_DIRECTORY_AREA_OFFSET
from .data_types import PATCH_DIRECTORY_ENTRY_SIZE
from .data_types import PATCH_PARAMETER_AREA_OFFSET
from .data_types import PATCH_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer
from .directory_area import DirectoryEntryStruct
from .parameter_area import PatchParamEntry
from .parameter_area import PatchParamEntryContainer
from .partial_entry import PartialEntryAdapter
from .partial_entry import PartialEntryStruct
from util.constructs import pass_expression_deeper
from util.constructs import SafeListConstruct
from util.constructs import UnsizedConstruct


def PatchEntryStruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0 <= obj < MAX_NUM_PATCH
        ),
        "index" / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (PATCH_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + PATCH_DIRECTORY_AREA_OFFSET,
            DirectoryEntryStruct
        ),
        "parameter" / Pointer(
            lambda this: \
                (PATCH_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + PATCH_PARAMETER_AREA_OFFSET,
            PatchParamEntry
        ),
        "partial_entries" / Lazy(SafeListConstruct(
            lambda this: len(this.parameter.partial_list),
            PartialEntryAdapter(PartialEntryStruct(lambda this: 
                this.parameter.partial_list[this._index]
            ))
        ))
    ))
    return result
@dataclass
class PatchEntryContainer:
    index: int
    directory: DirectoryEntryContainer
    parameter: PatchParamEntryContainer
    partial_entries: Callable


@dataclass
class PatchEntry(Traversable):
    directory_name: str
    parameter_name: str
    _f_partial_entries: Callable
    _parent: Optional[Element] = None
    _path: List[str] = field(default_factory=list)

    type_id: ClassVar[ElementTypes] = ElementTypes.DirectoryEntry
    type_name: ClassVar[str] = "Roland S-770 Patch"


    def __post_init__(self):
        self._partial_entries = None


    @property
    def name(self):
        result = self.directory_name
        return result
    

    @property
    def partial_entries(self):
        if not self._partial_entries:
            self._partial_entries = self._f_partial_entries()
        return self._partial_entries


    @property
    def children(self):
        result = list(self.partial_entries.values())
        return result


class PatchEntryAdapter(Adapter):


    def _decode(self, obj, context, path) -> PatchEntry:
        container = cast(PatchEntryContainer, obj)

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys():
            if "parent" in context._.keys():
                parent = cast(Element, context._.parent)
                element_path = parent.path
            if "fat" in context._.keys():
                context["fat"] = context._.fat

        name = container.directory.name
        patch_path = element_path + [name]

        patch = PatchEntry(
            container.directory.name,
            container.parameter.name,
            container.partial_entries,
            parent,
            patch_path
        )
        context["parent"] = patch
        
        return patch


    def _encode(self, obj, context, path):
        raise NotImplementedError

