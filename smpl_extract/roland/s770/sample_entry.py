import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from dataclasses import field
from io import IOBase
from construct.core import Adapter
from construct.core import Computed
from construct.core import Construct
from construct.core import ExprValidator
from construct.core import Pointer
from construct.core import Struct
from typing import ClassVar
from typing import List
from typing import Optional
from typing import cast

from base import Element, ElementTypes
from .data_types import MAX_NUM_SAMPLE, SAMPLE_DIRECTORY_AREA_OFFSET, SAMPLE_DIRECTORY_ENTRY_SIZE, SAMPLE_PARAMETER_AREA_OFFSET, SAMPLE_PARAMETER_ENTRY_SIZE
from .directory_area import DirectoryEntryContainer, DirectoryEntryStruct
from .fat import RolandFileAllocationTable
from .parameter_area import SampleParamEntryContainer, SampleParamEntryStruct

from util.constructs import UnsizedConstruct, pass_expression_deeper
from util.fat import FatNotPresent


def SampleEntryStruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: obj < MAX_NUM_SAMPLE
        ),
        "index" / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (SAMPLE_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + SAMPLE_DIRECTORY_AREA_OFFSET,
            DirectoryEntryStruct
        ),
        "parameter" / Pointer(
            lambda this: \
                (SAMPLE_PARAMETER_ENTRY_SIZE*new_index_expr(this)) \
                + SAMPLE_PARAMETER_AREA_OFFSET,
            SampleParamEntryStruct
        )
    ))
    return result
@dataclass
class SampleEntryContainer:
    index: int
    directory: DirectoryEntryContainer
    parameter: SampleParamEntryContainer


@dataclass
class SampleEntry:
    index: int
    directory_name: str
    parameter_name: str
    _data_stream: IOBase
    _parent: Optional[Element] = None
    _path: List[str] = field(default_factory=list)

    type_id: ClassVar[ElementTypes] = ElementTypes.DirectoryEntry
    type_name: ClassVar[str] = "Roland S-770 Sample"


    @property
    def name(self):
        result = self.directory_name
        return result


class SampleEntryAdapter(Adapter):


    def _decode(self, obj, context, path):
        container = cast(SampleEntryContainer, obj)

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys():
            if "parent" in context._.keys():
                parent = cast(Element, context._.parent)
                element_path = parent.path
            if "fat" in context._.keys():
                fat = cast(RolandFileAllocationTable, context._.fat)
            else:
                raise FatNotPresent
        else:
            raise FatNotPresent

        name = container.directory.name
        sample_path = element_path + [name]
        
        data_stream = fat.get_file(container.directory.fat_entry)
        result = SampleEntry(
            container.index,
            container.directory.name,
            container.parameter.name,
            data_stream,
            parent,
            sample_path
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError

