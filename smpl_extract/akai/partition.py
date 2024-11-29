from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import cast
from construct.core import Bytes
from construct.core import ConstructError
from construct.core import Const
from construct.core import Int8ul
from construct.core import Lazy
from construct.core import Rebuild
from construct.core import Struct
from construct.core import Int16ul
from construct.core import Computed
from construct.core import Tell
from construct.expr import this

from smpl_extract.base import Element
from smpl_extract.structural import T_ROUTINE
from smpl_extract.structural import Traversable
from smpl_extract.util.constructs import ChildInfo
from smpl_extract.util.constructs import ElementAdapter
from smpl_extract.util.stream import StreamOffset
from smpl_extract.util.stream import SubStreamConstruct

from .data_types import AKAI_PARTITION_MAGIC
from .data_types import AKAI_SAT_ENTRY_CNT
from .data_types import AKAI_SECTOR_SIZE
from .data_types import AKAI_VOLUME_ENTRY_CNT
from .data_types import InvalidCharacter
from .sat import SegmentAllocationTable
from .sat import SegmentAllocationTableAdapter
from .volume import Volume
from .volume import VolumeEntryConstruct
from .volume import VolumesAdapter


class InvalidPartition(Exception):
    pass


class Partition(Traversable):


    type_name: ClassVar[str] = "Partition"


    def __init__(
            self,
            f_sat: Callable[[], SegmentAllocationTable],
            f_volumes: Callable[[Dict[str, Any]], List[Element]],
            name: str,
            parent: Optional[Element] = None,
            path: Optional[List[str]] = None,
            routines: Optional[Dict[str, T_ROUTINE]] = None
    ) -> None:
        super().__init__(
            f_realize_children=f_volumes,
            routines=routines,
            path=path,
            parent=parent
        )
        self._f_sat = f_sat
        self._sat = None
        self.name = name

    
    @property
    def sat(self):
        if not self._sat:
            self._sat = self._f_sat()
        return self._sat


    @property
    def volumes(self):
        result = cast(List[Volume], self.children)
        return result


class PartitionAdapter(ElementAdapter):
    def _parse(self, stream, context, path):

        try:
            partition_container = self.subcon._parse(  # type: ignore
                stream,  
                context, 
                path
            )
        except InvalidCharacter:
            raise ConstructError

        if partition_container.header.size <= 0:
            raise ConstructError

        result = self._decode(partition_container, context, path)
        return result


    def _decode_element(
            self, 
            obj, 
            child_info: ChildInfo, 
            context: Dict[str, Any], 
            path: str
    ):
        del path  # unused
        partition_container = obj

        partition_name = child_info.name
        parent = child_info.parent
        element_path = child_info.next_path
        routines = child_info.routines

        if len(partition_name) > 0 and partition_name[-1] != ":":
            partition_name = partition_name + ":"

        partition = Partition(
            partition_container.sat,
            self.wrap_child_realization(
                partition_container.volumes,
                context
            ),
            partition_name,
            parent,
            element_path,
            routines=routines
        )
        
        return partition


    def _build(self, obj, stream, context, path):
        raise NotImplementedError


PartitionHeaderConstruct = Struct(
    "start_address" / Tell,
    "size" / Int16ul,
    "total_size" / Computed(this.size * AKAI_SECTOR_SIZE),
    "check_sum_x" / Computed(this.size//128 - 1),
    "partition_stream" / SubStreamConstruct(
        StreamOffset, 
        size=this.total_size, 
        offset=this.start_address
    ),
    Const(b"\x00\x00"),
    Const(AKAI_PARTITION_MAGIC),
    Rebuild(Int8ul, lambda this: 0x55 if this.check_sum_x % 2 == 0 else 0xD5),
    Rebuild(Int8ul, lambda this: this.check_sum_x//2 + 0xBA),
    Const(b"\x2F\x00"),
)


PartitionParser = PartitionAdapter(
    Struct(
        "header" / PartitionHeaderConstruct,
        "volume_entries" / VolumeEntryConstruct[AKAI_VOLUME_ENTRY_CNT],
        "sat" / SegmentAllocationTableAdapter(
            this.header.partition_stream,
            Int16ul[AKAI_SAT_ENTRY_CNT]  # type: ignore
        ),  
        "volumes" / Lazy(VolumesAdapter(  
            this.volume_entries,
            this.sat,  # type: ignore
            Lazy(Bytes(  # type: ignore
            lambda this: this.header.total_size \
                - PartitionHeaderConstruct.sizeof() \
                - VolumeEntryConstruct[AKAI_VOLUME_ENTRY_CNT].sizeof() \
                - Int16ul[AKAI_SAT_ENTRY_CNT].sizeof()
            )),
        ))  
    )
).compile()

