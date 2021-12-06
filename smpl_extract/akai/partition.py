import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
from typing import Callable
from typing import OrderedDict
from construct.core import Bytes
from construct.core import ConstructError
from construct.core import Lazy
from construct.core import Padding
from construct.core import Struct
from construct.core import Subconstruct
from construct.core import Int16ul
from construct.core import Computed
from construct.core import Tell
from construct.expr import this

from .data_types import AKAI_SAT_ENTRY_CNT
from .data_types import AKAI_SECTOR_SIZE
from .data_types import AKAI_VOLUME_ENTRY_CNT
from .data_types import InvalidCharacter
from .sat import SegmentAllocationTable
from .sat import SegmentAllocationTableAdapter
from .volume import Volume
from .volume import VolumeEntryConstruct
from .volume import VolumesAdapter
from util.stream import StreamOffset
from util.stream import SubStreamConstruct


class InvalidPartition(Exception):
    pass


class Partition:


    def __init__(
            self,
            f_sat: Callable[[], SegmentAllocationTable],
            f_volumes: Callable[[], OrderedDict[str, Volume]],
            name: str = ""
    ) -> None:
        self._f_sat = f_sat
        self._sat = None
        self._f_volumes = f_volumes
        self._volumes = None
        self.name = name
        self.type = "Partition"

    
    @property
    def sat(self):
        if not self._sat:
            self._sat = self._f_sat()
        return self._sat


    @property
    def volumes(self):
        if not self._volumes:
            self._volumes = self._f_volumes()
        return self._volumes


    @property
    def children(self):
        return self.volumes


class PartitionConstructAdapter(Subconstruct):
    def _parse(self, stream, context, path):

        try:
            partition_container = self.subcon._parse(stream, context, path)
        except InvalidCharacter:
            raise ConstructError

        if partition_container.header.size <= 0:
            raise ConstructError

        partition_name = context["name"]

        partition = Partition(
            partition_container.sat,
            partition_container.volumes,
            partition_name
        )
        
        return partition


    def _build(self, obj, stream, context, path):
        raise NotImplementedError


PartitionHeaderConstruct = Struct(
    "start_address" / Tell,
    "size" / Int16ul,
    "total_size" / Computed(this.size * AKAI_SECTOR_SIZE),
    Padding(200),
    "partition_stream" / SubStreamConstruct(
        StreamOffset, 
        size=this.total_size, 
        offset=this.start_address
    )
).compile()



PartitionConstruct = PartitionConstructAdapter(
    Struct(
        "header" / PartitionHeaderConstruct,
        "volume_entries" / VolumeEntryConstruct[AKAI_VOLUME_ENTRY_CNT],
        "sat" / SegmentAllocationTableAdapter(
            this.header.partition_stream,
            Int16ul[AKAI_SAT_ENTRY_CNT]
        ),  
        "volumes" / Lazy(VolumesAdapter(
            this.volume_entries,
            this.sat,
            Lazy(Bytes(
            lambda this: this.header.total_size \
                - PartitionHeaderConstruct.sizeof() \
                - VolumeEntryConstruct[AKAI_VOLUME_ENTRY_CNT].sizeof() \
                - Int16ul[AKAI_SAT_ENTRY_CNT].sizeof()
            )),
        ))
    )
).compile()

