from construct.core import ConstructError
from io import IOBase
from io import SEEK_END
from io import SEEK_SET
from typing import List, cast

from smpl_extract.base import ElementTypes
from smpl_extract.structural import Image

from .partition import InvalidPartition
from .partition import Partition
from .partition import PartitionParser


class AkaiImageParser(Image):


    name = "AKAI Image"
    type_name = "AKAI Image"
    type_id = ElementTypes.DirectoryEntry


    def __init__(
            self,
            file: IOBase
    ) -> None:
        self.file = file
        # get files size
        self.file_size = self.file.seek(0, SEEK_END)
        self.file.seek(0, SEEK_SET)

        self._partitions = []
        self._partitions_loaded_flag = False


    def _load_partitions(self):
        partition_cnt = 0
        partitions = []
        while self.file.tell() < self.file_size:
            name = chr(ord("A") + partition_cnt)
            try:
                partition = PartitionParser.parse_stream(
                    self.file,  # type: ignore
                    _elem_name=name,
                    _elem_parent=self,
                    _elem_routines=self._routines
                )  
            except (InvalidPartition, ConstructError) as e:
                break
            partitions.append(partition)
            partition_cnt += 1

        for routine in self._routines.values():
            partitions = routine(partitions)
        self._partitions = cast(List[Partition], partitions)
        self._partitions_loaded_flag = True

    
    @property
    def partitions(self)->List[Partition]:
        if not self._partitions_loaded_flag:
            self._load_partitions()
        return self._partitions

    
    @property
    def children(self):
        return self.partitions


    def _sanitize_string(
            self, 
            input_str: str
    ):
        result = input_str.upper().strip()
        if len(result) > 0 and result[-1] == ":":
            result = result[:-1]
        return result

