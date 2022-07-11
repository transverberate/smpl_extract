import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
import enum


class Endianess(enum.IntEnum):
    LITTLE  = enum.auto()
    BIG     = enum.auto()


@dataclass(repr=True, eq=True, frozen=True)
class StreamEncoding:
    endianess:                  Endianess = Endianess.LITTLE
    sample_width:               int = 1
    num_interleaved_channels:   int = 0  # less than 2 -> unused

