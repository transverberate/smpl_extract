import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

from dataclasses import dataclass
from io import IOBase
from typing import List, cast
from construct.core import Adapter
from construct.core import ConstructError
from construct.core import Int16ul
from construct.core import Padding
from construct.core import Struct
from construct.core import Union

from .data_types import FAT_AREA_ID
from .data_types import DATA_FAT_OFFSET
from .data_types import FAT_ERROR_FLAG
from .data_types import FAT_FREE_FLAG
from .data_types import FAT_IS_END_F
from .data_types import FAT_NUM_ENTRIES
from .data_types import FAT_RESERVED_FLAG
from .data_types import FAT_VERSION_1_FLAG
from .data_types import FAT_VERSION_2_FLAG
from .data_types import ROLAND_CLUSTER_SIZE
from util.fat import FileAllocationTable
from util.fat import FileStream
from util.fat import SectorLink
from util.fat import add_to_sector_links
from util.stream import StreamOffset
from util.stream import StreamSizeConstruct
from util.stream import StreamWrapper
from util.stream import SubStreamConstruct


FatAreaStruct = Union(
    0,
    "fat_entries" / Int16ul[FAT_NUM_ENTRIES],
    "metadata" / Struct(
        "fat_id" / Int16ul,
        "num_unused_clusters" / Int16ul,
        Padding(2 * (FAT_NUM_ENTRIES-4)),
        "version_flag_1" / Int16ul,
        "version_flag_2" / Int16ul
    ),
    "stream_size" / StreamSizeConstruct,
    "fat_data_stream"  / SubStreamConstruct(
        StreamOffset,
        size=(lambda this: this.stream_size-DATA_FAT_OFFSET),
        offset=DATA_FAT_OFFSET
    ),
)
@dataclass
class FatAreaMetadataContainer:
    fat_id: int
    num_unused_clusters: int
    version_flag_1: int
    version_flag_2: int
@dataclass
class FatAreaContainer:
    fat_entries: List[int]
    metadata: FatAreaMetadataContainer
    stream_size: int
    fat_data_stream: StreamWrapper


class RolandFile(FileStream):


    def __init__(
            self,
            partition_stream:   IOBase,
            sector_list:        List[int],
            position:           int = 0,
            buffer_length:      int = 0x1000
    ) -> None:
        super().__init__(
            partition_stream, 
            sector_size=ROLAND_CLUSTER_SIZE,
            sector_list=sector_list,
            position=position,
            buffer_length=buffer_length
        )


class RolandFileAllocationTable(FileAllocationTable):
    def get_file(self, index: int) -> RolandFile:
        sector_list = self.get_path(index)
        result = RolandFile(
            self.parent_stream,
            sector_list
        )
        return result


@dataclass
class FatArea:
    version:                int
    num_remaining_clusters: int
    fat:                    RolandFileAllocationTable


class FatAreaAdapter(Adapter):


    def _decode(self, obj, context, path) -> FatArea:
        container = cast(FatAreaContainer, obj)

        fat_id = container.metadata.fat_id
        if fat_id != FAT_AREA_ID:
            raise ConstructError((
                "Bad FAT identifier. "
                f"Expected {FAT_AREA_ID}, found {fat_id}"
            ))

        num_remaining_clusters = container.metadata.num_unused_clusters

        version_flag_1 = container.metadata.version_flag_1
        version_flag_2 = container.metadata.version_flag_2
        
        version_map = {
            FAT_VERSION_1_FLAG: 1,
            FAT_VERSION_2_FLAG: 2
        }

        version = 1

        for version_flag in (version_flag_1, version_flag_2):
            if version_flag != FAT_VERSION_1_FLAG:
                if version_flag not in version_map.keys():
                    raise ConstructError((
                        f"Unknown FAT version {version_flag}."
                    ))
                version = version_map[version_flag]
                break

        fat_entries = container.fat_entries

        sector_links = [SectorLink()] * FAT_NUM_ENTRIES
        dirty_flags = [False] * FAT_NUM_ENTRIES
        dirty_flags[0:2] = [True, True]
        for i in range(2, FAT_NUM_ENTRIES - 9):

            if dirty_flags[i]:
                continue

            subpath_links = []
            subpath_index = i
            while True:
                if subpath_index >= FAT_NUM_ENTRIES:
                    break
                
                value = fat_entries[subpath_index]
                dirty_flags[subpath_index] = True

                if value == FAT_ERROR_FLAG:
                    raise ConstructError("Encountered ERROR_FLAG in FAT.")
                    
                if value in (FAT_RESERVED_FLAG, FAT_FREE_FLAG):
                    if len(subpath_links) > 0:
                        if value == FAT_RESERVED_FLAG:
                            err_type = "RESERVE_FLAG"  
                        else:
                            err_type = "FREE_FLAG"
                        raise ConstructError(f"Unexpected {err_type} in FAT.")
                    else:
                        break

                subpath_links.append(subpath_index)

                if FAT_IS_END_F(value):
                    add_to_sector_links(subpath_links, sector_links)
                    break

                subpath_index = value
                continue

        fat = RolandFileAllocationTable(
            container.fat_data_stream, 
            FAT_NUM_ENTRIES, 
            sector_links
        )

        result = FatArea(
            version,
            num_remaining_clusters,
            fat
        )
        return result


    def _encode(self, obj, context, path):
        raise NotImplementedError


FatAreaParser = FatAreaAdapter(FatAreaStruct)

