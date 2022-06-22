import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from construct.core import Adapter
from dataclasses import dataclass
from dataclasses import field
from typing import cast
from typing import ClassVar
from typing import List
from typing import Optional

from base import Element
from elements import ProgramElement
from .partial_entry import PartialParamCommon
from .partial_entry import PartialParamSampleSectionCommon
from .patch_entry import PatchEntry
from .patch_entry import PatchParamEntryCommon
from util.dataclass import get_common_field_args
from util.dataclass import make_itemizable


@make_itemizable
@dataclass
class SampleReferenceItem(PartialParamSampleSectionCommon):
    sample: str = ""


@make_itemizable
@dataclass
class PartialItem(PartialParamCommon):
    samples: List = field(default_factory=list)


@make_itemizable
@dataclass
class ProgramFile(PatchParamEntryCommon,  ProgramElement):
    name:               str                     = ""
    partials:           List[PartialItem]       = field(default_factory=list)
    _parent:            Optional[Element]       = None
    _path:              List[str]               = field(default_factory=list)

    type_name:          ClassVar[str]           = "Roland S-7xx Program"


    # needed to stop unimplemented abstract method exception
    # will be added by @make_itemizable
    def itemize(self):
        return None


class ProgramFileAdapter(Adapter):


    def _decode(self, obj, context, path) -> ProgramFile:
        patch_entry = cast(PatchEntry, obj)
        patch_args = get_common_field_args(
            PatchParamEntryCommon,
            patch_entry
        )

        partial_items = []

        for partial_entry in patch_entry.partial_entries.values():
            partial_args = get_common_field_args(
                PartialParamCommon,
                partial_entry
            )

            sample_items = []
            for sample_ref_entry in partial_entry.sample_entry_references:
                sample_ref_args = get_common_field_args(
                    PartialParamSampleSectionCommon,
                    sample_ref_entry,
                )
                sample_name = sample_ref_entry.sample_entry.name
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

