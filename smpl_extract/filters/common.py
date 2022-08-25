import os, sys
from typing import Tuple
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

import struct
import numpy as np

from fir import FirFilter
from iir import IirFilter


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


class ChickSysCustomDeemphFilter(IirFilter):


    def __init__(self, coeffs: Tuple[float, float, float]) -> None:
        B = np.asarray([coeffs[0], coeffs[1]])
        A = np.asarray([1.0, -coeffs[2]])
        super().__init__(B, A)


    def fix_iteration(self, x):
        # bound result
        result = x
        if np.abs(x) > 32767:
            result = np.sign(x) * 32767
        return result


    def fix_type(self, x):
        # mimics the behavior of VBA's FixInt
        result = np.sign(x) * np.floor(np.abs(x))
        return result

    

class ChickSysStandardDeemphFilter(ChickSysCustomDeemphFilter):
    def __init__(self) -> None:
        super().__init__((
            0.5923,  # exact coefficient precision
            0.1516, 
            0.2560
        ))


class ChickSysDarkerDeemphFilter(ChickSysCustomDeemphFilter):
    def __init__(self) -> None:
        super().__init__((
            0.7071,  # exact coefficient precision
            0.1213, 
            0.1716
        ))


class ChickSysSpecialDeemphFilter(ChickSysCustomDeemphFilter):
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
    dtype=np.int32  # headspace for multiplication results
)
_chick_sys_roland_deemph_k_gain = 52067 # DC offset -> np.sum(_roland_deemph_h)
_chick_sys_roland_deemph_delay_offset = 7
class ChickSysRolandDeemphFilter(FirFilter):
    

    def __init__(self) -> None:
        super().__init__(
            _chick_sys_roland_deemph_h, 
            _chick_sys_roland_deemph_delay_offset
        )
    

    # Would benefit (likely substantially) from Cython or C extension
    def convolve_valid(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:

        # this implementation presumes len(x) > len(h)
        # else the convolution is invalid
        if len(h) > len(x):
            y = np.asarray([], dtype=np.int16)
            return y

        x = x.astype(dtype=np.int16)

        k = _chick_sys_roland_deemph_k_gain     # Constant
        n_x = len(x)                            # Constant
        n_h = len(h)                            # Constant
        n_y = max(0, n_x - n_h + 1)             # Constant
        
        h_ubound_inclusive = n_h - 1            # Constant
        x_ubound_exclusive = n_h                # Variable

        y = np.zeros(n_y, dtype=np.int16)
        for i in range(n_y):

            y_cur = int(0)
            # h is being 'flipped' by starting the index at
            # the upper bound an decrementing.
            # The kernel used for h, however, is symmetric 
            # so this doesn't really matter...
            h_index = h_ubound_inclusive
            for x_index in range(i, x_ubound_exclusive):
                # For accurate recreation of ChickenSys's 'authentic' filter:
                # The division by k_gain needs to happen before 
                # summing to y_cur - rather than summing first and
                # then dividing the summed y_cur by k_gain. 
                # Due to integer rounding, these two methods produce
                # slightly different answers, with the former giving
                # the expected result.
                # This is the reason for this entire custom convolution
                # routine.
                # Amusingly, Translator doesn't use proper integer division
                # and incurs typecast to double then rounds to the
                # nears int
                y_cur += np.round(int(x[x_index] * h[h_index]) / k)
                h_index -= 1

            if y_cur > 32767:
                y_cur = 32767
            elif y_cur < -32768:
                y_cur = -32768
            
            y[i] = int(y_cur)
            x_ubound_exclusive += 1
        
        return y

