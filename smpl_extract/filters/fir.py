
from typing import Optional
import numpy as np


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

