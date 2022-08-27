import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

import numpy as np
import numpy.typing as npt
from typing import List
import unittest

from smpl_extract.filters.fir import FirFilter
from smpl_extract.filters.iir import CircularBufferDouble
from smpl_extract.filters.iir import IirFilter


def make_array(x: List, dtype: npt.DTypeLike = np.int32):
    result = np.asarray(x, dtype=dtype)
    return result


def arrays_are_equal(a, b):
    if np.size(a) != np.size(b):
        return False
    if a.dtype == np.float64:
        result = np.allclose(a, b)
    else:
        result = np.all(a == b)
    return result


class Filters_Test(unittest.TestCase):

    # --- FIR Filter ---

    def test_fir_causal_process(self):
        h = make_array([-1, 2, -1])
        deemph = FirFilter(h)
        x1 = make_array([1, 2, 3, 4, 5, 6, 7, 8])
        x2 = make_array([8, 7, 6, 5, 4, 3, 2, 1])
        y_expected = make_array(
            [-1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
        )

        y_result = deemph.process(x1)
        y_result = np.concatenate([y_result, deemph.process(x2)])

        self.assertTrue(arrays_are_equal(y_expected, y_result))


    def test_fir_causal_get_remaining(self):
        h = make_array([-1, 2, -1])
        deemph = FirFilter(h)
        x1 = make_array([1, 2, 3, 4, 5, 6, 7, 8])
        x2 = make_array([8, 7, 6, 5, 4, 3, 2, 1])
        r_expected = make_array([])

        deemph.process(x1)
        deemph.process(x2)
        r_result = deemph.get_remaining()

        self.assertTrue(arrays_are_equal(r_expected, r_result))


    def test_fir_noncausal_process(self):
        h = make_array([-1, 2, -1])
        deemph = FirFilter(h, delay_offset=2)
        x1 = make_array([1, 2, 3, 4, 5, 6, 7, 8])
        x2 = make_array([8, 7, 6, 5, 4, 3, 2, 1])
        y_expected = make_array(
            [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
        )

        y_result = deemph.process(x1)
        y_result = np.concatenate([y_result, deemph.process(x2)])

        self.assertTrue(arrays_are_equal(y_expected, y_result))


    def test_fir_noncausal_get_remaining(self):
        h = make_array([-1, 2, -1])
        deemph = FirFilter(h, delay_offset=2)
        x1 = make_array([1, 2, 3, 4, 5, 6, 7, 8])
        x2 = make_array([8, 7, 6, 5, 4, 3, 2, 1])
        r_expected = make_array([0, -1])

        deemph.process(x1)
        deemph.process(x2)
        r_result = deemph.get_remaining()

        self.assertTrue(arrays_are_equal(r_expected, r_result))


    def test_fir_reset_state(self):
        h = make_array([-1, 2, -1])
        deemph = FirFilter(h)
        x1 = make_array([1, 2, 3, 4, 5, 6, 7, 8])
        x2 = make_array([8, 7, 6, 5, 4, 3, 2, 1])
        y_expected = make_array([-8, 9, 0, 0, 0, 0, 0, 0])

        deemph.process(x1)
        deemph.reset_state()
        y_result = deemph.process(x2)

        self.assertTrue(arrays_are_equal(y_expected, y_result))


    # -- IIR Filter Circular Buffer ---

    def test_cbuffer_init_is_zeroes(self):
        expected = make_array([0, 0, 0], dtype=np.float64)
        cbuff = CircularBufferDouble(size=3)
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_init_from_array(self):
        expected = make_array([4, 5, 6], dtype=np.float64)
        cbuff = CircularBufferDouble(x=make_array([4, 5, 6], dtype=np.float64))
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_init_from_undersized_array(self):
        expected = make_array([4, 5, 6], dtype=np.float64)
        cbuff = CircularBufferDouble(
            size=2, 
            x=make_array([4, 5, 6], dtype=np.float64)
        )
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_init_from_oversized_array(self):
        expected = make_array([4, 5, 6, 0], dtype=np.float64)
        cbuff = CircularBufferDouble(
            size=4, 
            x=make_array([4, 5, 6], dtype=np.float64)
        )
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))
        

    def test_cbuffer_push(self):
        expected = make_array([3, 0, 0], dtype=np.float64)
        cbuff = CircularBufferDouble(size=3)
        cbuff.push(3)
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_push_moves_current_values(self):
        expected = make_array([4, 1, 2, 3], dtype=np.float64)
        cbuff = CircularBufferDouble(
            size=4,
            x=make_array([1, 2, 3], dtype=np.float64)
        )
        cbuff.push(4)
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_push_moves_wrap_around(self):
        expected = make_array([4, 1, 2], dtype=np.float64)
        cbuff = CircularBufferDouble(
            size=3,
            x=make_array([1, 2, 3], dtype=np.float64) 
        )
        cbuff.push(4)
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_push_moves_wrap_around_refill(self):
        expected = make_array([7, 6, 5], dtype=np.float64)
        cbuff = CircularBufferDouble(
            size=3,
            x=make_array([1, 2, 3], dtype=np.float64)
        )
        cbuff.push(4)
        cbuff.push(5)
        cbuff.push(6)
        cbuff.push(7)
        result = cbuff.to_array()
        self.assertTrue(arrays_are_equal(expected, result))


    def test_cbuffer_inner_product(self):
        expected = 2.0
        A = make_array([1, 2, -1], dtype=np.float64)
        cbuff = CircularBufferDouble(
            size=3,
            x=make_array([1, 2, 3], dtype=np.float64)
        )
        
        result = cbuff.inner_prod(A)
        self.assertAlmostEqual(expected, result)


    # -- IIR Filter ---

    def test_iir_first_order_process(self):
        B = make_array([0.5, -0.1240], np.float64)  # type: ignore
        A = make_array([1.0, -0.5488], np.float64)  # type: ignore
        deemph = IirFilter(B, A)
        x1 = make_array(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 
            np.float64  # type: ignore
        ) 
        x2 = make_array(
            [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], 
            np.float64  # type: ignore
        )
        y_expected = make_array(
            [
                0.500000000000000,
                1.150400000000000,
                1.883339520000000,
                2.661576728576000,
                3.464673308642508,
                4.281412711783008,
                5.105639296226515,
                5.933974845769112,
                6.264565395358089,
                5.945993488972519,
                5.395161226748119,
                4.716864481239368,
                3.968615227304165,
                3.181976036744525,
                2.374268448965395,
                1.554998524792209
            ],
            np.float64  # type: ignore    
        )
        
        y_result = deemph.process(x1)
        y_result = np.concatenate([y_result, deemph.process(x2)])

        self.assertTrue(arrays_are_equal(y_expected, y_result))


    def test_iir_first_order_get_remaining(self):
        B = make_array([0.5, -0.1240], np.float64)  # type: ignore
        A = make_array([1.0, -0.5488], np.float64)  # type: ignore
        deemph = IirFilter(B, A)
        x1 = make_array(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 
            np.float64  # type: ignore
        ) 
        x2 = make_array(
            [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], 
            np.float64  # type: ignore
        )
        r_expected = make_array([])

        deemph.process(x1)
        deemph.process(x2)
        r_result = deemph.get_remaining()

        self.assertTrue(arrays_are_equal(r_expected, r_result))


    def test_iir_reset_state(self):
        B = make_array([0.5, -0.1240], np.float64)  # type: ignore
        A = make_array([1.0, -0.5488], np.float64)  # type: ignore
        deemph = IirFilter(B, A)
        x1 = make_array(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 
            np.float64  # type: ignore
        ) 
        x2 = make_array(
            [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], 
            np.float64  # type: ignore
        )
        y_expected = make_array(
            [
                0.500000000000000,
                1.150400000000000,
                1.883339520000000,
                2.661576728576000,
                3.464673308642508,
                4.281412711783008,
                5.105639296226515,
                5.933974845769112,
                4.000000000000000,
                4.703200000000000,
                4.713116160000000,
                4.342558148608000,
                3.763195911956070,
                3.069241916481491,
                2.312399963765042,
                1.521045100114255
            ],
            np.float64  # type: ignore    
        )
        
        y_result = deemph.process(x1)
        deemph.reset_state()
        y_result = np.concatenate([y_result, deemph.process(x2)])

        self.assertTrue(arrays_are_equal(y_expected, y_result))



if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit as err:
        pass
    pass

