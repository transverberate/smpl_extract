import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
from typing import Dict, List, cast
from typing import Iterable
from typing import Optional
from typing import OrderedDict
from construct.core import Adapter
from construct.core import Computed
from construct.core import ConstructError
from construct.core import Int16ul
from construct.core import Struct
from construct.lib.containers import Container
from construct.expr import this

from .akai_string import AkaiPaddedString
from base import Element
from elements import Traversable
from .data_types import VolumeType
from .file_entry import FileEntriesAdapter
from .file_entry import FileEntryConstruct
from .file_entry import InvalidFileEntry
from .file_entry import FileEntry
from util.constructs import EnumWrapper


class Volume(Traversable):


    def __init__(
            self,
            name: str = "",
            parent: Optional[Element] = None,
            path: Optional[List[str]] = None,
            volume_type: VolumeType = VolumeType.INACTIVE,
            file_entries: Optional[List[FileEntry]] = None
    ) -> None:
        self.name = name
        self.volume_type = volume_type
        self.type_name = str(volume_type or "AKAI Volume")
        self.file_entries = file_entries or []
        self._is_files_realized = False
        self._files = []
        self._parent = parent
        self._path = path or []


    def _realize_files(self):
        for file_entry in self.file_entries:
            try:
                file = file_entry.file
            except (InvalidFileEntry, ConstructError) as e:
                file = None

            if file is not None:
                self._files.append(file)
        self._is_files_realized = True

        
    @property
    def files(self)->List[FileEntry]:
        if not self._is_files_realized:
            self._realize_files()
        return self._files


    @property
    def children(self):
        return self.files


VolumeBodyConstruct = result = Struct(
    "file_entries" / FileEntriesAdapter(this._.sat, FileEntryConstruct),
)
@dataclass
class VolumeBodyContainer(Container):
    file_entries: Iterable[FileEntry]


VolumeEntryConstruct = Struct(
    "name" / AkaiPaddedString(12),
    "type_raw" / Int16ul,
    "type" / EnumWrapper(Computed(this.type_raw & 0xFF), VolumeType),
    "start" / Int16ul
).compile()
@dataclass
class VolumeEntryContainer(Container):
    name:   str
    type:   VolumeType
    start:  int


class VolumesAdapter(Adapter):


    def __init__(
            self,
            volume_entries, 
            sat, 
            subcon
    ):
        super().__init__(subcon)  # type: ignore
        self.volume_entries = volume_entries
        self.sat = sat


    def _decode(self, obj, context, path)->List[Volume]:
        del obj, path  # Unused

        if callable(self.volume_entries):
            volume_entries = self.volume_entries(context) 
        else:
            volume_entries = self.volume_entries 
        sat = self.sat(context) if callable(self.sat) else self.sat

        parent: Optional[Element] = None
        element_path = []
        if "_" in context.keys() and "parent" in context._.keys():
            parent = cast(Element, context._.parent)
            element_path = parent.path

        volumes: List[Volume] = list()
        for volume_entry in volume_entries:
            volume_type = volume_entry.type
            
            if volume_type != VolumeType.INACTIVE:
                name            = volume_entry.name
                volume_sector   = volume_entry.start
                volume_stream = sat.get_segment(volume_sector)
                volume_path = element_path + [name]

                volume = Volume(
                    name,
                    parent,
                    volume_path,
                    volume_type
                )

                volume_body = VolumeBodyConstruct.parse_stream(
                    volume_stream,
                    _=context,
                    sat=sat,
                    parent=volume
                )

                if volume_body is None:
                    raise ConstructError

                file_entries = volume_body.file_entries
                volume.file_entries = file_entries

                volumes.append(volume)

        return volumes


    def _encode(self, obj, context, path):
        raise NotImplementedError

