import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

import numpy as np
import struct

from smpl_extract.filters.fir import ChickSysCustomFirFilter
from smpl_extract.filters.fir import FirFilter
from smpl_extract.filters.iir import ChickSysCustomIirFilter


def _bytes_to_double(x: bytes) -> float:
    y = struct.unpack(">d", x)[0]
    return y


# --- CDXtract ---

_cdxtract_roland_deemph_h = np.asarray(
    [
        _bytes_to_double(b"\x3F\x74\xC0\x29\x80\x53\x00\xA6"),  # 0.005066072573015534
        _bytes_to_double(b"\x3F\xD4\x32\xA8\x65\x50\xCA\xA2"),  # 0.315591906491287
        _bytes_to_double(b"\x3F\xE3\x50\xE6\xA1\xCD\x43\x9B"),  # 0.6036255989257485
        _bytes_to_double(b"\x3F\xB3\x62\x26\xC4\x4D\x88\x9B"),  # 0.07571642200994903
        0.0,
        0.0,
        0.0,
        0.0
    ], 
    dtype=np.double
)
class CdXtractRolandDeemphFilter(FirFilter):
    def __init__(self) -> None:
        super().__init__(_cdxtract_roland_deemph_h)


# --- ChickenSys ---

class ChickSysStandardDeemphFilter(ChickSysCustomIirFilter):
    def __init__(self) -> None:
        super().__init__((
            0.5923,  # exact coefficient precision
            0.1516, 
            0.2560
        ))


class ChickSysDarkerDeemphFilter(ChickSysCustomIirFilter):
    def __init__(self) -> None:
        super().__init__((
            0.7071,  # exact coefficient precision
            0.1213, 
            0.1716
        ))


class ChickSysSpecialDeemphFilter(ChickSysCustomIirFilter):
    def __init__(self) -> None:
        super().__init__((
            1.0 * 22082/32767,  # fractions needed for precision
            1.0 *  4967/32767,
            1.0 *  8411/32767
        ))


_chick_sys_roland_deemph_h = np.asarray(
    [
        1,
       -2,
        5,
      -11,
       25,
      -65,
      176,
     -460,
     9981,
    32767,
     9981,
     -460,
      176,
      -65,
       25,
      -11,
        5,
       -2,
        1
    ],
    dtype=np.int16
)
_chick_sys_roland_deemph_k_gain = 52067  # DC offset -> np.sum(_roland_deemph_h)
_chick_sys_roland_deemph_delay_offset = 7
class ChickSysRolandDeemphFilter(ChickSysCustomFirFilter):
    

    def __init__(self) -> None:
        super().__init__(
            _chick_sys_roland_deemph_h, 
            _chick_sys_roland_deemph_delay_offset,
            _chick_sys_roland_deemph_k_gain
        )

