import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
import collections
from dataclasses import dataclass
from typing import Dict
from typing import Iterable
from typing import OrderedDict
from construct.core import Adapter
from construct.core import ConstructError
from construct.core import Int16ul
from construct.core import Struct
from construct.lib.containers import Container
from construct.expr import this

from .data_types import VolumeType
from .akai_string import AkaiPaddedString
from .file_entry import FileEntriesAdapter
from .file_entry import FileEntryConstruct
from .file_entry import InvalidFileEntry
from .file_entry import FileEntry
from util.constructs import EnumWrapper


class Volume:


    def __init__(
            self,
            name: str = "",
            volume_type: VolumeType = VolumeType.INACTIVE,
            file_entries: Iterable[FileEntry] = None
    ) -> None:
        
        self.name = name
        self.volume_type = volume_type
        self._file_entries = file_entries or []
        self._is_files_realized = False
        self._files = {}


    def _realize_files(self):
        for file_entry in self._file_entries:
            try:
                file = file_entry.file
            except (InvalidFileEntry, ConstructError):
                file = None

            if file is not None:
                self._files[file_entry.name] = file_entry
        self._is_files_realized = True

        
    @property
    def files(self)->Dict[str, FileEntry]:
        if not self._is_files_realized:
            self._realize_files()
        return self._files

    @property
    def children(self):
        return self.files

    @property
    def type(self):
        return self.volume_type.to_string()


VolumeBodyConstruct = result = Struct(
    "file_entries" / FileEntriesAdapter(this._.sat, FileEntryConstruct),
)
@dataclass
class VolumeBodyContainer(Container):
    file_entries: Iterable[FileEntry]

VolumeEntryConstruct = Struct(
    "name" / AkaiPaddedString(12),
    "type" / EnumWrapper(Int16ul, VolumeType),
    "start" / Int16ul
).compile()
@dataclass
class VolumeEntryContainer(Container):
    name:   str
    type:   VolumeType
    start:  int


class VolumesAdapter(Adapter):


    def __init__(self, volume_entries, sat, subcon):
        super().__init__(subcon)
        self.volume_entries = volume_entries
        self.sat = sat

    def _decode(self, obj, context, path)->OrderedDict[str, Volume]:
        del obj, path  # Unused

        if callable(self.volume_entries):
            volume_entries = self.volume_entries(context) 
        else:
            volume_entries = self.volume_entries 
        sat = self.sat(context) if callable(self.sat) else self.sat

        volumes: OrderedDict[str, Volume] = collections.OrderedDict()
        for volume_entry in volume_entries:
            volume_type = volume_entry.type
            
            if volume_type != VolumeType.INACTIVE:
                name            = volume_entry.name
                volume_sector   = volume_entry.start
                volume_stream = sat.get_segment(volume_sector)

                volume_body = VolumeBodyConstruct.parse_stream(
                    volume_stream,
                    _=context,
                    sat=sat
                )

                if volume_body is None:
                    raise ConstructError

                file_entries = volume_body.file_entries

                volume = Volume(
                    name,
                    volume_type,
                    file_entries
                )

                volumes[name] = volume

        return volumes


    def _encode(self, obj, context, path):
        raise NotImplementedError

