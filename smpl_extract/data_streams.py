import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
import enum
from io import IOBase
import numpy as np
from typing import cast
from typing import Dict


class IncompatibleNumberOfChannels(Exception): ...
class NoDataStream(Exception): ...


class Endianess(enum.IntEnum):
    LITTLE  = enum.auto()
    BIG     = enum.auto()


system_byte_order = Endianess.BIG if sys.byteorder == "big" \
    else Endianess.LITTLE


@dataclass(repr=True, frozen=True)
class StreamEncoding:
    endianess:                  Endianess = Endianess.LITTLE
    sample_width:               int = 1
    num_interleaved_channels:   int = 1
    is_signed:                  bool = True


    @property
    def is_interleaved(self):
        result = self.num_interleaved_channels > 1
        return result


    @property
    def dtype(self) -> np.dtype:
        if self.is_signed:
            default = np.dtype("int16")
            mapping: Dict[int, np.dtype] = {
                1:  np.dtype("int8"),
                2:  np.dtype("int16"),
                4:  np.dtype("int32"),
                8:  np.dtype("int64")
            }
        else:
            default = np.dtype("uint8")
            mapping: Dict[int, np.dtype] = {
                1:  np.dtype("uint8"),
                2:  np.dtype("uint16"),
                4:  np.dtype("uint32"),
                8:  np.dtype("uint64")
            }
        result = mapping.get(self.sample_width, default)
        return result


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StreamEncoding):
            return False
        other = cast(StreamEncoding, other)
        common_checks = (
            self.endianess == other.endianess,
            self.sample_width == other.sample_width,
            self.is_signed == other.is_signed,
            self.is_interleaved == other.is_interleaved
        )
        if not all(common_checks):
            return False
        
        if self.is_interleaved:
            if self.num_interleaved_channels != other.num_interleaved_channels:
                return False

        return True


@dataclass
class DataStream:
    stream:     IOBase
    encoding:   StreamEncoding = StreamEncoding()


    def __post_init__(self):
        enc = self.encoding
        self.frame_size = enc.num_interleaved_channels * enc.sample_width

