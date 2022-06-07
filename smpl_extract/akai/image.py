import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from construct.core import ConstructError
from io import IOBase
from io import SEEK_END
from io import SEEK_SET
from typing import List

from elements import ElementTypes
from elements import Traversable
from .partition import InvalidPartition
from .partition import Partition
from .partition import PartitionConstruct


class AkaiImage(Traversable):


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

        self._path = []
        self._parent = None


    def _load_partitions(self):
        partition_cnt = 0
        while self.file.tell() < self.file_size:
            name = chr(ord("A") + partition_cnt)
            try:
                partition = PartitionConstruct.parse_stream(
                    self.file,  # type: ignore
                    name=name,
                    parent=self
                )  
            except (InvalidPartition, ConstructError):
                break
            self._partitions.append(partition)
            partition_cnt += 1

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

