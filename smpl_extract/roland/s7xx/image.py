from dataclasses import dataclass
from construct.core import Adapter
from construct.core import Computed
from construct.core import ConstructError
from construct.core import FixedSized
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Seek
from construct.core import Struct
from io import SEEK_SET
from io import IOBase
import re
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Match
from typing import cast

from smpl_extract.base import Element
from smpl_extract.base import ElementTypes
from smpl_extract.structural import Image
from smpl_extract.structural import T_ROUTINE
from smpl_extract.util.constructs import ChildInfo
from smpl_extract.util.constructs import ElementAdapter

from .data_types import FAT_AREA_OFFSET
from .data_types import ID_AREA_SIZE
from .fat import FatArea
from .fat import FatAreaParser
from .fat import RolandFileAllocationTable
from .volume_entry import VolumeEntry
from .volume_entry import VolumeEntriesList


IdAreaStruct = Struct(
    "revision" / Int32ul,
    "s7xx_str" / PaddedString(10, encoding="ascii"),
    Padding(2),
    "empty_str" / PaddedString(15, encoding="ascii"),
    Padding(1),
    "version_str" / PaddedString(31, encoding="ascii"),
    Padding(1),
    "copyright_str" / PaddedString(31, encoding="ascii"),
    Padding(1),
    Padding(160),
    "disk_name" / PaddedString(16, encoding="ascii"),
    "disk_capacity" / Int32ul,
    "num_volumes" / Int16ul,
    "num_performances" / Int16ul,
    "num_patches" / Int16ul,
    "num_partials" / Int16ul,
    "num_samples" / Int16ul,
    # 226 Bytes Remaining
)
@dataclass
class IdAreaContainer:
    revision: int
    s7xx_str: str
    empty_str: str 
    version_str: str
    copyright_str: str
    disk_name: str
    disk_capacity: int
    num_volumes: int
    num_performances: int
    num_patches: int
    num_partials: int
    num_samples: int


@dataclass
class IdArea:
    revision: int
    model_version: str
    disk_type: str
    disk_version: str
    disk_name: str
    disk_capacity: int
    num_volumes: int
    num_performances: int
    num_patches: int
    num_partials: int
    num_samples: int


class IdAreaAdapter(Adapter):


    _S7XX_REGEX = re.compile(r"\s*S7\d\d\s+MR25A", flags=re.I)
    _VERSION_REGEX = re.compile(
        r"\s*([Ss][A-z]*-\d+)\s+([A-z\s\-]*?Disk)\s?([A-z\s]*?)\s+Ver\.?\s*(\d(\.\d+)?[\w-]*)\s*",
        flags=re.I
    )
    _COPYRIGHT_REGEX = re.compile(r"\s*Copyright\s+Roland", flags=re.I)


    def _decode(self, obj, context, path) -> IdArea:
        del context, path  # unused

        container = cast(IdAreaContainer, obj)
        
        verifications = (
            (container.s7xx_str, self._S7XX_REGEX),
            (container.version_str, self._VERSION_REGEX),
            (container.copyright_str, self._COPYRIGHT_REGEX)
        )
        match_results: List[Match[str]] = []

        for test_str, regex in verifications:
            match_result = regex.match(test_str)
            if not match_result:
                raise ConstructError

            match_results.append(match_result)

        model_version = match_results[1].groups()[0]
        disk_type = match_results[1].groups()[1]
        disk_version = match_results[1].groups()[3]

        result = IdArea(
            revision=container.revision,
            model_version=model_version,
            disk_type=disk_type,
            disk_version=disk_version,
            disk_name=container.disk_name,
            disk_capacity=container.disk_capacity,
            num_volumes=container.num_volumes,
            num_performances=container.num_performances,
            num_patches=container.num_patches,
            num_partials=container.num_partials,
            num_samples=container.num_samples
        )

        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError


IdAreaAdapterParser = IdAreaAdapter(IdAreaStruct)


def is_roland_s7xx_image(stream: IOBase)->bool:
    stream_head = stream.tell()
    stream.seek(0, SEEK_SET)

    result = True
    try:
        IdAreaAdapterParser.parse_stream(stream)  # type: ignore
    except (ConstructError, UnicodeDecodeError) as e:
        result = False 

    stream.seek(stream_head, SEEK_SET)
    return result


RolandS7xxImageStruct = Struct(
    "id_area" / FixedSized(ID_AREA_SIZE, IdAreaAdapterParser),
    Seek(FAT_AREA_OFFSET),
    "fat_area" / FatAreaParser,
    "fat" / Computed(lambda this: this.fat_area.fat),
    "_dir_version" / Computed(lambda this: this.fat_area.version),
    "volumes" / VolumeEntriesList(
        lambda this: this.id_area.num_volumes,
        lambda this: this.id_area.num_performances
    )  # type: ignore
)
@dataclass
class RolandS7xxImageContainer:
    id_area: IdArea
    fat_area: FatArea
    fat: RolandFileAllocationTable
    volumes: List[VolumeEntry]


@dataclass
class RolandS7xxImage(Image): 


    revision: int
    model_version: str
    disk_type: str
    disk_version: str
    disk_name: str
    disk_capacity: int
    num_volumes: int
    num_performances: int
    num_patches: int
    num_partials: int
    num_samples: int
    volumes: List[VolumeEntry]
    fat: RolandFileAllocationTable

    _f_realize_children: Callable[[Dict[str, Any]], Element]

    name: ClassVar = "Roland S-7xx Image"
    type_name: ClassVar = "Roland S-7xx Image"
    type_id: ClassVar = ElementTypes.DirectoryEntry


    def set_routines(self, routines: Dict[str, T_ROUTINE]):
        super().set_routines(routines)
        for volume in self.volumes:
            volume.set_routines(self._routines)

    
    def __post_init__(self):
        self._children = None
    

class RolandS7xxImageAdapter(ElementAdapter):
    

    def _decode_element(
            self, 
            obj, 
            child_info: ChildInfo, 
            context: Dict[str, Any], 
            path: str
    ):
        del child_info, path

        container = cast(RolandS7xxImageContainer, obj)
        result = RolandS7xxImage(
            container.id_area.revision,
            container.id_area.model_version,
            container.id_area.disk_type,
            container.id_area.disk_version,
            container.id_area.disk_name,
            container.id_area.disk_capacity,
            container.id_area.num_volumes,
            container.id_area.num_performances,
            container.id_area.num_patches,
            container.id_area.num_partials,
            container.id_area.num_samples,
            container.volumes,
            container.fat,
            _f_realize_children=self.wrap_child_realization(  # type: ignore
                lambda: container.volumes,  # type: ignore
                context
            )
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError


def RolandSxxImageParser(file) -> RolandS7xxImage:
    adapter = RolandS7xxImageAdapter(
        RolandS7xxImageStruct
    )
    result = adapter.parse_stream(file)
    return result

