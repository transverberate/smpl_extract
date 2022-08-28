#!python
#cython: language_level=3

cimport cython
import numpy as np
from typing import Optional

from libc.math cimport round as cround


class FirFilter:


    def __init__(self, h: np.ndarray, delay_offset: int = 0) -> None:
        self.N = len(h)
        self.h = h
        self.m0 = delay_offset
        self.m1 = self.N - self.m0 - 1
        self.x_prev = np.zeros(self.m1)


    def reset_state(self, **kwargs): 
        x_prev = kwargs.get("x_prev", None)
        x_prev = x_prev or np.zeros(self.m1)
        self.x_prev = x_prev


    def convolve_valid(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:
        if np.size(x) < np.size(h):
            return np.asarray([], dtype=x.dtype)
        y = np.convolve(x, h, "valid")
        return y


    def process(self, x: np.ndarray) -> np.ndarray:
        dtype = x.dtype
        x_full = np.concatenate([self.x_prev, x])
        self.x_prev = x[-(self.N - 1):]
        y = self.convolve_valid(x_full, self.h).astype(dtype)
        return y


    def get_remaining(self) -> np.ndarray:
        dtype = self.x_prev.dtype
        x_full = np.concatenate([self.x_prev, np.zeros(self.m0)])
        y = self.convolve_valid(x_full, self.h).astype(dtype)
        self.reset_state()
        return y


# -- Chicken Sys --


cdef short _c_bound_and_fix(double x):
    cdef short result = 0
    if x > 32767.0:
        result = 32767
        return result
    # yes - this lbound IS -32768
    if x < -32768.0:  
        result = -32768
        return result
    
    result = <short> cround(x)
    return result


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef _c_chicken_sys_convolve_valid(
    short[:] x, 
    short[:] h,
    int k
):

    assert k != 0
    cdef size_t n_x = x.shape[0]                # Constant
    cdef size_t n_h = h.shape[0]                # Constant

    # this implementation presumes len(x) > len(h)
    # else the convolution is invalid
    if n_h > n_x:
        y = np.asarray([], dtype=np.int16)
        return y

    cdef size_t n_y = n_x - n_h + 1             # Constant
    if n_y < 0:
        n_y = 0
    
    cdef size_t h_ubound_inclusive = n_h - 1    # Constant
    cdef size_t x_ubound_exclusive = n_h        # Variable

    # malloc result
    y = np.zeros(n_y, dtype=np.int16)
    cdef short[:] y_view = y 
    
    cdef size_t h_index = 0
    cdef size_t x_index = 0
    cdef double y_cur = 0.0
    cdef short y_final = 0

    cdef size_t i

    for i in range(n_y):

        y_cur = 0.0
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
            # and incurs a typecast to double then rounds to the
            # nears int
            y_cur += cround(<double>((<int>x[x_index]) * (<int>h[h_index])) / k)
            h_index -= 1

        y_final = _c_bound_and_fix(y_cur)
        
        y_view[i] = y_final
        x_ubound_exclusive += 1
    
    return y


class ChickSysCustomFirFilter(FirFilter):
    

    def __init__(
        self,
        h: np.ndarray,
        delay_offset: int = 0,
        k_gain: int = 1
    ) -> None:
        super().__init__(h, delay_offset)
        self.k_gain = k_gain
    

    def convolve_valid(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:
        x = x.astype(np.int16)
        result = _c_chicken_sys_convolve_valid(x, h, self.k_gain)
        return result

