#!python
#cython: language_level=3

cimport cython
import numpy as np
from typing import Tuple

from libc.math cimport trunc
from libc.stdlib cimport free
from libc.stdlib cimport malloc


# -- Circular Buffer (cbuffer)  ---

cdef struct s_double_cbuffer:
    double *arr
    size_t N
    size_t cur_pos


cdef void init_double_cbuffer(s_double_cbuffer *cbuffer, double[:] x, size_t N):
    cdef size_t num_x = x.size
    if N < num_x:
        N = num_x

    cdef double *arr = <double *> malloc(
        N * sizeof(double))
    if not arr:
        raise MemoryError()
    
    cbuffer.N = N
    cbuffer.arr = arr
    cdef size_t i = 0
    for i in range(num_x):
        cbuffer.arr[i] = x[i]
    for i in range(num_x, N):
        cbuffer.arr[i] = 0.0
    cbuffer.cur_pos = 0


cdef void free_double_cbuffer(s_double_cbuffer *cbuffer):
    free(cbuffer.arr)


cdef void push_double_cbuffer(s_double_cbuffer *cbuffer, double a):
    if cbuffer.cur_pos == 0:
        cbuffer.cur_pos = cbuffer.N - 1
    else:
        cbuffer.cur_pos -= 1
    
    cbuffer.arr[cbuffer.cur_pos] = a
    pass


# DANGEROUS CALL: 
# BEFORE CALLING
# Ensure that len(A) <= len(cbuffer.arr) 
@cython.boundscheck(False)
@cython.wraparound(False)
cdef double inner_prod_double_cbuffer(s_double_cbuffer *cbuffer, double[:] A):
    cdef size_t num_A = A.shape[0]
    cdef size_t buffer_index = cbuffer.cur_pos
    cdef double y = 0.0
    for i in range(num_A):
        y += A[i] * cbuffer.arr[buffer_index]
        buffer_index += 1
        if buffer_index >= cbuffer.N:
            buffer_index = 0
    return y


cdef void fill_arr_double_cbuffer(s_double_cbuffer *cbuffer, double[:] y):
    cdef size_t num_y = y.size
    assert cbuffer.N >= num_y
    
    cdef size_t buffer_index = cbuffer.cur_pos
    for i in range(num_y):
        y[i] = cbuffer.arr[buffer_index]
        buffer_index += 1
        if buffer_index >= cbuffer.N:
            buffer_index = 0


cdef class CircularBufferDouble:
    cdef s_double_cbuffer cbuffer

    def __cinit__(self, size: int = 0, x = None):
        if x is None:
            x = np.asarray([])
        elif size < x.shape[0]:
            size = x.shape[0]
        init_double_cbuffer(&self.cbuffer, x, size)


    def push(self, value: float):
        push_double_cbuffer(&self.cbuffer, value)


    def inner_prod(self, A: np.ndarray):
        assert A.size <= self.cbuffer.N
        y = inner_prod_double_cbuffer(&self.cbuffer, A)
        return y


    def to_array(self):
        x = np.zeros((self.cbuffer.N,), dtype=np.float64)
        fill_arr_double_cbuffer(&self.cbuffer, x)
        return x


    def __str__(self):
        x = self.to_array()
        result = str(x)
        return result


    def __dealloc__(self):
        free_double_cbuffer(&self.cbuffer)


#  -- IIR Filtering ---

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def _c_process(
        double[:] x,
        double[:] y,
        double[:] B,
        double[:] A,
        double[:] x_prev,
        double[:] y_prev
):

    cdef size_t num_x = x.shape[0]
    cdef size_t num_y = y.shape[0]
    cdef size_t num_A = A.shape[0]
    cdef size_t num_B = B.shape[0]
    cdef size_t num_x_prev = x_prev.shape[0]
    cdef size_t num_y_prev = y_prev.shape[0]

    assert num_A > 0
    assert num_B > 0
    assert num_x == num_y

    # x_window
    cdef size_t num_x_window = num_x_prev + 1
    cdef s_double_cbuffer x_window
    init_double_cbuffer(&x_window, x_prev, num_x_window)

    # y_window
    cdef size_t num_y_window = num_y_prev
    cdef s_double_cbuffer y_window
    init_double_cbuffer(&y_window, y_prev, num_y_window)

    cdef double[:] A_true = A[1:]
    cdef double k_gain = A[0]
    cdef size_t A_true_size = A_true.shape[0]
    
    cdef double y_cur = 0.0
    cdef size_t i = 0

    try:
        assert k_gain != 0.0
        assert x_window.N == B.shape[0]
        assert y_window.N == A_true.shape[0]

        # perform iterations
        for i in range(num_x):
            push_double_cbuffer(&x_window, x[i])
            y_cur = inner_prod_double_cbuffer(&x_window, B) \
                - inner_prod_double_cbuffer(&y_window, A_true)
            y_cur /= k_gain

            push_double_cbuffer(&y_window, y_cur)
            y[i] = y_cur

        # save state
        fill_arr_double_cbuffer(&x_window, x_prev)
        fill_arr_double_cbuffer(&y_window, y_prev)

    finally:
        # free mem
        free_double_cbuffer(&x_window)
        free_double_cbuffer(&y_window)


class IirFilter:


    def __init__(self, B: np.ndarray, A: np.ndarray) -> None:
        self.B = B
        self.A = A
        self.n_x_prev = max(0, len(B) - 1)
        self.n_y_prev = max(0, len(A) - 1)
        self.reset_state()


    def reset_state(
            self, 
            **kwargs
        ): 
        pass
        x_prev = kwargs.get("x_prev", None)
        y_prev = kwargs.get("y_prev", None)
        x_prev = x_prev or np.zeros(self.n_x_prev, dtype=np.float64)
        y_prev = y_prev or np.zeros(self.n_y_prev, dtype=np.float64)
        self.x_prev = x_prev.astype(np.float64)
        self.y_prev = y_prev.astype(np.float64)


    def process(self, x: np.ndarray) -> np.ndarray:
        x = x.astype(dtype=np.float64)
        y = np.zeros((x.size,)).astype(np.float64)
        _c_process(
            x,
            y,
            self.B,
            self.A,
            self.x_prev,
            self.y_prev
        )
        return y
        

    def get_remaining(self) -> np.ndarray:
        y = np.zeros((0,), dtype=np.float64)
        self.reset_state()
        return y


# -- ChickenSys IIR --

# mimics VBA's FixInt employed by Translator
cdef short _c_fix_int(double x):
    result = <short> trunc(x)
    return result


cdef double _c_bound(double x):
    cdef double result = x
    if x > 32767.0:
        result = 32767.0
    # yes - this IS supposed to be -32767, not -32768
    # yes - it is strange
    elif x < -32767.0:  
        result = -32767.0
    return result


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def _c_chickensys_process(
        short[:] x,
        short[:] y,
        double[:] B,
        double[:] A,
        double[:] x_prev,
        double[:] y_prev
):
    cdef size_t num_x = x.shape[0]
    cdef size_t num_y = y.shape[0]
    cdef size_t num_A = A.shape[0]
    cdef size_t num_B = B.shape[0]
    cdef size_t num_x_prev = x_prev.shape[0]
    cdef size_t num_y_prev = y_prev.shape[0]

    assert num_A > 0
    assert num_B > 0
    assert num_x == num_y

    # x_window
    cdef size_t num_x_window = num_x_prev + 1
    cdef s_double_cbuffer x_window
    init_double_cbuffer(&x_window, x_prev, num_x_window)

    # y_window
    cdef size_t num_y_window = num_y_prev
    cdef s_double_cbuffer y_window
    init_double_cbuffer(&y_window, y_prev, num_y_window)
    
    cdef double[:] A_true = A[1:]
    cdef double k_gain = A[0]
    cdef size_t A_true_size = A_true.shape[0]

    cdef double x_cur = 0.0
    cdef double y_cur = 0.0
    cdef short y_final = 0
    cdef size_t i = 0

    try:
        assert k_gain != 0.0
        assert x_window.N == B.shape[0]
        assert y_window.N == A_true.shape[0]

        # perform iterations
        for i in range(num_x):
            x_cur = <double> x[i]
            push_double_cbuffer(&x_window, x_cur)
            y_cur = inner_prod_double_cbuffer(&x_window, B) \
                - inner_prod_double_cbuffer(&y_window, A_true)
            y_cur /= k_gain

            y_cur = _c_bound(y_cur)
            push_double_cbuffer(&y_window, y_cur)

            y_final = _c_fix_int(y_cur)
            y[i] = y_final

        # save state
        fill_arr_double_cbuffer(&x_window, x_prev)
        fill_arr_double_cbuffer(&y_window, y_prev)

    finally:
        # free mem
        free_double_cbuffer(&x_window)
        free_double_cbuffer(&y_window)


class ChickSysCustomIirFilter(IirFilter):


    def __init__(self, coeffs: Tuple[float, float, float]) -> None:
        B = np.asarray([coeffs[0], coeffs[1]])
        A = np.asarray([1.0, -coeffs[2]])
        super().__init__(B, A)


    def process(self, x: np.ndarray) -> np.ndarray:
        y = np.zeros((x.size,)).astype(np.int16)
        _c_chickensys_process(
            x,
            y,
            self.B,
            self.A,
            self.x_prev,
            self.y_prev
        )
        y = y.astype(np.int16)
        return y

