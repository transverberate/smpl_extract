from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import cast
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional

from smpl_extract.base import Element
from smpl_extract.structural import ProgramElement
from smpl_extract.util.constructs import ChildInfo
from smpl_extract.util.constructs import ElementAdapter
from smpl_extract.util.dataclass import get_common_field_args

from .partial_entry import PartialParamCommon
from .partial_entry import PartialParamSampleSectionCommon
from .patch_entry import PatchEntry
from .patch_entry import PatchParamEntryCommon


@dataclass
class SampleReferenceItem(PartialParamSampleSectionCommon):
    sample: str = ""


@dataclass
class PartialItem(PartialParamCommon):
    samples: List = field(default_factory=list)


@dataclass
class ProgramFile(PatchParamEntryCommon,  ProgramElement):
    name:               str                     = ""
    partials:           List[PartialItem]       = field(default_factory=list)
    _parent:            Optional[Element]       = None
    _path:              List[str]               = field(default_factory=list)

    type_name:          ClassVar[str]           = "Roland S-7xx Program"


class ProgramFileAdapter(ElementAdapter):


    def _decode_element(
            self, 
            obj, 
            child_info: ChildInfo, 
            context: Dict[str, Any], 
            path: str
        ) -> ProgramFile:
        del child_info, context, path

        patch_entry = cast(PatchEntry, obj)
        patch_args = get_common_field_args(
            PatchParamEntryCommon,
            patch_entry
        )

        partial_items = []

        for partial_entry in patch_entry.partial_entries:
            partial_args = get_common_field_args(
                PartialParamCommon,
                partial_entry
            )

            sample_items = []
            partial_entry.sample_entries  # needed to ensure routines are run
            for sample_ref_entry in partial_entry.sample_entry_references:
                sample_ref_args = get_common_field_args(
                    PartialParamSampleSectionCommon,
                    sample_ref_entry,
                )
                sample_name = sample_ref_entry.sample_entry.safe_name
                sample_item = SampleReferenceItem(
                    **sample_ref_args,
                    sample=sample_name
                )
                sample_items.append(sample_item)

            partial_item = PartialItem(
                **partial_args,
                samples=sample_items
            )
            partial_items.append(partial_item)
        
        program_file = ProgramFile(
            name=patch_entry.name,
            **patch_args,
            partials=partial_items,
            _parent=patch_entry._parent,  # type: ignore
            _path=patch_entry._path
        ) 

        return program_file


    def _encode(self, obj, context, path):
        return super()._encode(obj, context, path)

