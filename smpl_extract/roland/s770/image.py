import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
import re
from typing import List
from typing import Match
from typing import cast
from construct.core import Adapter
from construct.core import ConstructError
from construct.core import FixedSized
from construct.core import Int16ul
from construct.core import Int32ul
from construct.core import PaddedString
from construct.core import Padding
from construct.core import Struct

from .data_types import ID_AREA_SIZE


IdAreaStruct = Struct(
    "revision" / Int32ul,
    "s770_str" / PaddedString(10, encoding="ascii"),
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
    s770_str: str
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
    disk_version: float
    disk_name: str
    disk_capacity: int
    num_volumes: int
    num_performances: int
    num_patches: int
    num_partials: int
    num_samples: int


class IdAreaAdapter(Adapter):


    _S770_REGEX = re.compile(r"\s*S770\s+MR25A", flags=re.I)
    _VERSION_REGEX = re.compile(
        r"\s*(S-\d+)\s+(\w+)\s+Disk\s+Ver\.?\s+(\d(\.\d+)?)\s*",
        flags=re.I
    )
    _COPYRIGHT_REGEX = re.compile(r"\s*Copyright\s+Roland", flags=re.I)


    def _decode(self, obj, context, path) -> IdArea:
        del context, path  # unused

        container = cast(IdAreaContainer, obj)
        
        verifications = (
            (container.s770_str, self._S770_REGEX),
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
        disk_version = float(match_results[1].groups()[2])

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


IdAreaAdapterStruct = IdAreaAdapter(IdAreaStruct)


RolandS770ImageStruct = Struct(
    "id_area" / FixedSized(ID_AREA_SIZE, IdAreaStruct),
)

