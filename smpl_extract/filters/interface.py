import numpy as np
from typing import Protocol


class DigitalFilter(Protocol):
    def reset_state(self, **kwargs): ...

    def process(self, x: np.ndarray) -> np.ndarray: ...

    def get_remaining(self) -> np.ndarray: ...

