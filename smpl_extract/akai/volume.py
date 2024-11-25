import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from construct.core import Computed
from construct.core import ConstructError
from construct.core import Int16ul
from construct.core import Struct
from construct.lib.containers import Container
from construct.expr import this

from .akai_string import AkaiPaddedString
from base import Element
from .data_types import VolumeType
from .file_entry import FileEntriesAdapter
from .file_entry import FileEntryConstruct
from .file_entry import InvalidFileEntry
from .file_entry import FileEntry
from structural import T_ROUTINE
from structural import Traversable
from util.constructs import ChildInfo
from util.constructs import ElementAdapter
from util.constructs import EnumWrapper


class Volume(Traversable):


    def __init__(
            self,
            name: str = "",
            volume_type: VolumeType = VolumeType.INACTIVE,
            parent: Optional[Element] = None,
            path: Optional[List[str]] = None,
            routines: Optional[Dict[str, T_ROUTINE]] = None,
            file_entries: Optional[List[FileEntry]] = None
    ) -> None:
        super().__init__(
            f_realize_children=lambda x: [],
            routines=routines,
            path=path,
            parent=parent,
            type_name=str(volume_type or "AKAI Volume")
        )
        self.name = name
        self.volume_type = volume_type
        self.file_entries = file_entries or []
        self._is_files_realized = False
        self._files = []


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
    def files(self) -> List[FileEntry]:
        if not self._is_files_realized:
            self._realize_files()
            files = self._files
            for routine in self._routines.values():
                files = routine(files)
            self._files = files
        return self._files  # type: ignore


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
    "type" / EnumWrapper(Computed(this.type_raw & 0x03), VolumeType),
    "start" / Int16ul
).compile()
@dataclass
class VolumeEntryContainer(Container):
    name:   str
    type:   VolumeType
    start:  int


class VolumesAdapter(ElementAdapter):


    def __init__(
            self,
            volume_entries, 
            sat, 
            subcon
    ):
        super().__init__(subcon)
        self.volume_entries = volume_entries
        self.sat = sat


    def _decode_element(
            self, 
            obj, 
            child_info: ChildInfo, 
            context: Dict[str, Any], 
            path: str
    ) -> List[Volume]:
    
        del obj, path  # Unused

        if callable(self.volume_entries):
            volume_entries = self.volume_entries(context) 
        else:
            volume_entries = self.volume_entries 
        sat = self.sat(context) if callable(self.sat) else self.sat

        parent = child_info.parent
        parent_path = child_info.parent_path

        volumes: List[Volume] = list()
        for volume_entry in volume_entries:
            volume_type = volume_entry.type
            
            if volume_type != VolumeType.INACTIVE:
                name            = volume_entry.name
                volume_sector   = volume_entry.start
                volume_stream = sat.get_segment(volume_sector)
                volume_path = parent_path + [name]

                volume = Volume(
                    name=name,
                    volume_type=volume_type,
                    parent=parent,
                    path=volume_path,
                    routines=child_info.routines
                )

                volume_body = VolumeBodyConstruct.parse_stream(
                    volume_stream,
                    _=context,
                    sat=sat,
                    _elem_parent=volume,
                    _elem_routines=child_info.routines
                )

                if volume_body is None:
                    raise ConstructError

                file_entries = volume_body.file_entries
                volume.file_entries = file_entries

                volumes.append(volume)

        return volumes


    def _encode(self, obj, context, path):
        raise NotImplementedError

