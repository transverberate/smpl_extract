import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from io import SEEK_END, SEEK_SET, BufferedIOBase

from typing import Dict, List
import re

from .partition import InvalidPartition, Partition


class InvalidPathStr(Exception):
    pass


class AkaiImage:

    def __init__(
            self,
            file: BufferedIOBase
    ) -> None:
        self.file = file
        self.name = "root"
        self.type = "Image"

        # get files size
        self.file_size = self.file.seek(0, SEEK_END)
        self.file.seek(0, SEEK_SET)

        self._partitions = {}
        self._partitions_loaded_flag = False


    def _load_partitions(self):
        partition_cnt = 0
        while self.file.tell() < self.file_size:
            name = chr( ord("A") + partition_cnt )
            try:
                partition = Partition.from_raw_stream(
                    self.file, 
                    name=name,
                    total_filesize=self.file_size
                )
            except InvalidPartition:
                break

            self._partitions[name] = partition

            # seek to next partition
            self.file.seek(partition.size + partition.physical_address, SEEK_SET)
            partition_cnt += 1

        self._partitions_loaded_flag = True

    
    @property
    def partitions(self)->Dict[str, Partition]:
        if not self._partitions_loaded_flag:
            self._load_partitions()
        return self._partitions

    
    @property
    def children(self):
        return self.partitions


    _TOKENIZE_PATH_REGEX = re.compile(r"\:?(\\{1,2}|\/)")


    def get_node_from_path(self, path_str: str):
        tokens_raw = self._TOKENIZE_PATH_REGEX.split(path_str.strip())
        tokens_raw_iter = iter(tokens_raw)

        tokens: List[str] = []
        tokens.append(next(tokens_raw_iter))
        while True:
            try:
                next(tokens_raw_iter)
                next_token = next(tokens_raw_iter)
            except StopIteration:
                break
            tokens.append(next_token)

        if len(tokens) > 0 and len(tokens[-1]) < 1:
            tokens = tokens[:-1]
        if len(tokens) > 0:
            tokens[0] = tokens[0].replace(":", "")

        current_node = self
        for i in range(len(tokens)):
            token = tokens[i]
            token_upper = token.upper()

            if (not hasattr(current_node, "children") or token_upper not in current_node.children.keys()):
                if len(tokens) > 0:
                    tokens[0] = tokens[0] + ":"
                path_so_far = "/".join(tokens[:i]) + "/" if current_node != self else "image"
                raise InvalidPathStr(f"The enitity \"{token}\" was not found in \"{path_so_far}\".")

            current_node = current_node.children[token_upper]
        
        return current_node
