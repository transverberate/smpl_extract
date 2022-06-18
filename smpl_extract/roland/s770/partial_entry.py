import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from dataclasses import field
from construct.core import Computed
from construct.core import Construct
from construct.core import ConstructError
from construct.core import ExprValidator
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
from .directory_area import DirectoryEntryStruct
from .parameter_area import PartialParamEntryContainer
from .parameter_area import PartialParamEntryStruct
from .parameter_area import PartialParamSampleSectionContainer
from .sample_entry import SampleEntryAdapter
from .sample_entry import SampleEntryContainer
from .sample_entry import SampleEntryStruct
from util.constructs import pass_expression_deeper
from util.constructs import UnsizedConstruct


def PartialEntryStruct(index_expr) -> Construct:
    new_index_expr = pass_expression_deeper(index_expr)

    result = UnsizedConstruct(Struct(
        ExprValidator(
            Computed(lambda this: new_index_expr(this)), 
            lambda obj, ctx: 0<= obj < MAX_NUM_PARTIAL
        ),
        "index" / Computed(new_index_expr),
        "directory" / Pointer(
            lambda this: \
                (PARTIAL_DIRECTORY_ENTRY_SIZE*new_index_expr(this)) \
                    + PARTIAL_DIRECTORY_AREA_OFFSET,
            DirectoryEntryStruct
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
    index: int
    directory: DirectoryEntryContainer
    parameter: PartialParamEntryContainer


@dataclass
class SampleEntryReference:
    sample_entry: SampleEntryContainer
    pitch_kf: int
    sample_level: int
    pan: int
    coarse_tune: int
    fine_tune: int
    smt_velocity_lower: int
    smt_fade_with_lower: int
    smt_velocity_upper: int
    smt_fade_with_upper: int


class SampleEntryReferenceAdapter(Subconstruct):


    def _parse(self, stream, context, path):
        container = cast(
            PartialParamSampleSectionContainer, 
            context["ref_container"]
        )
        if container.sample_selection < 0:
            raise ConstructError
        sample_entry_sc = SampleEntryAdapter(
            SampleEntryStruct(container.sample_selection)
        )
        sample_entry = sample_entry_sc._parse(  # type: ignore
            stream, 
            context, 
            path
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
    directory_name: str
    parameter_name: str
    sample_entry_references: List[SampleEntryReference]
    _parent: Optional[Element] = None
    _path: List[str] = field(default_factory=list)

    type_id: ClassVar[ElementTypes] = ElementTypes.DirectoryEntry
    type_name: ClassVar[str] = "Roland S-770 Partial"


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


    def _parse(self, stream, context, path):
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
        adapter = SampleEntryReferenceAdapter(Pass)
        for ref_container in sample_ref_containers:
            ctx = context.copy()
            ctx["ref_container"] = ref_container
            try:
                sample_reference = adapter._parse(stream, ctx, path)  # type: ignore
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
        
        return partial


    def _encode(self, obj, context, path):
        raise NotImplementedError

