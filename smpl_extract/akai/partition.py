import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from math import floor, ceil
from typing import Callable, Dict, List
from io import BufferedIOBase, BufferedReader

from .segments import SegmentAllocationTable, RequestedInvalidSector
from .data_types import AKAI_SECTOR_SIZE, SegmentAllocationTableConstruct, PartitionHeaderConstruct, VolumeEntriesConstruct, InvalidCharacter, VolumeType
from .volume import Volume
from .partition_reader import PartitionFileStream
from .file_entry import FileEntry

class InvalidPartition(Exception):
    pass


class Partition:


    def __init__(
            self,
            physical_address: int,
            size: int,
            file_allocation_table: SegmentAllocationTable,
            name: str = "",
            load_volumes_func: Callable[['Partition'], Dict[str, Volume]] = None
    ) -> None:
        self.physical_address = physical_address
        self.size = size
        self.file_allocation_table = file_allocation_table
        self.name = name
        self.type = "AKAI Partition"
        self._volumes = {}
        self._volumes_loaded_flag = False
        self._load_volumes_func = load_volumes_func or (lambda x: self._volumes)


    def _load_volumes(self):
        self._volumes = self._load_volumes_func(self)
        self._volumes_loaded_flag = True


    @property
    def volumes(self)->Dict[str, Volume]:
        if not self._volumes_loaded_flag:
            self._load_volumes()
        return self._volumes

    
    @property
    def children(self):
        return self.volumes


    def _get_segment_at_sector(
            self, 
            image_file: BufferedIOBase,
            sector: int
    )->BufferedIOBase:

        sector_map = self.file_allocation_table.get_path(sector)
        if sector_map is None:
            raise Exception(f"No Segment at sector {sector}")
        
        partition_segment = PartitionFileStream(
            image_file, 
            self.physical_address, 
            sector_map
        )
        return partition_segment

    
    def _realize_volume_file(
        self, 
        image_file: BufferedIOBase,
        file_entry: FileEntry
    ):

        # realize files in volume
        file_sector = file_entry.sector
        get_file_stream: Callable[[BufferedIOBase], BufferedIOBase] = \
            lambda image_file_inner: self._get_segment_at_sector(image_file_inner, file_sector)

        physical_address = self.physical_address + (AKAI_SECTOR_SIZE * file_sector)
        try:
            file_entry._realize_file_callback(
                get_file_stream(image_file),
                physical_address,
                get_file_stream
            )
        except (RequestedInvalidSector, InvalidCharacter):
            file_entry.invalid = True
    

    @classmethod
    def from_raw_stream(
            cls, 
            image_file: BufferedIOBase,
            name: str = "",
            total_filesize: int = None
    )->'Partition':

        physical_address = image_file.tell()
        header = PartitionHeaderConstruct.parse_stream(image_file)
        partition_size = header.size * AKAI_SECTOR_SIZE
        if (
                total_filesize is not None 
                and physical_address + partition_size > total_filesize
        ):
            raise InvalidPartition

        # Parse
        try:
            volume_entries_struct = VolumeEntriesConstruct.parse_stream(image_file)
        except InvalidCharacter:
            raise InvalidPartition

        # File Allocation Table FAT
        fat_struct = SegmentAllocationTableConstruct.parse_stream(image_file)
        fat = SegmentAllocationTable.from_raw_stream(fat_struct.fat)

        # add volumes func
        def load_volumes_func(
            image_file_inner: BufferedIOBase,
            volume_entries,
            partition_inner: Partition
        ):
            volumes = {}
            for volume_entry_struct in volume_entries:
                volume_type = volume_entry_struct.type
                
                if volume_type != VolumeType.INACTIVE:
                    name            = volume_entry_struct.name
                    volume_sector   = volume_entry_struct.start

                    volume_header_segment = partition._get_segment_at_sector(
                        image_file, 
                        volume_sector
                    )

                    volume = Volume.from_raw_stream(
                        volume_header_segment,
                        name,
                        volume_sector,
                        volume_type,
                        lambda file_entry: partition_inner._realize_volume_file(
                            image_file_inner,
                            file_entry
                        )
                    )

                    volumes[volume.name] = volume

            return volumes

        # init partition instance
        partition = cls(
            physical_address, 
            partition_size, 
            fat, 
            name,
            lambda partition_inner: load_volumes_func(
                image_file,
                volume_entries_struct.volume_entries,
                partition_inner
            )
        )

        return partition