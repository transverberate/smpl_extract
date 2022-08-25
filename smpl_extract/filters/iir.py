import numpy as np
from typing import Optional


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
        x_prev = kwargs.get("x_prev", None)
        y_prev = kwargs.get("y_prev", None)
        self.x_prev = x_prev or np.zeros(self.n_x_prev)
        self.y_prev = y_prev or np.zeros(self.n_y_prev)


    def fix_iteration(self, x):
        result = x
        return result


    def fix_type(self, x):
        result = x
        return result


    # Would benefit from Cython/C extension
    def process(self, x: np.ndarray) -> np.ndarray:
        dtype = x.dtype
        k_gain = self.A[0]
        A = self.A[1:]
        B = self.B
        x_window = np.concatenate([self.x_prev, [0]])
        y_prev = self.y_prev

        y = np.zeros(x.size).astype(A.dtype)
        for i, x_cur in enumerate(x):
            x_window = np.concatenate([[x_cur], x_window[:-1]])
            y_cur = np.inner(B, x_window.astype(B.dtype)) \
                - np.inner(A, y_prev.astype(A.dtype))
            y_cur /= k_gain

            y_cur = self.fix_iteration(y_cur)
            y_prev = np.concatenate([[y_cur], y_prev[:-1]])
            
            y_cur = self.fix_type(y_cur)
            y[i] = y_cur
        
        x_prev = x_window[:-1]
        self.x_prev = x_prev
        self.y_prev = y_prev

        y = y.astype(dtype)
        return y


    def get_remaining(self) -> np.ndarray:
        dtype = self.x_prev.dtype
        y = np.zeros(0, dtype)
        self.reset_state()
        return y

