import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from collections.abc import Iterable
from dataclasses import fields
from dataclasses import is_dataclass
import functools
from typing import Any 
from typing import Protocol
from typing import cast
from typing import Dict
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import Union


ItemT = Union[Mapping[str, 'ItemT'], Tuple['ItemT', ...], str]


class Itemizable(Protocol):
    def itemize(self) -> ItemT: ...


def itemize(self: Union[Sequence[Any], Dict[str, Any]])->ItemT:


    def process_value(value)->Union[str, ItemT]:
        result: Union[str, ItemT]
        if hasattr(value, "itemize"):
            result = cast(ItemT, value.itemize())
        elif not isinstance(value, str) and isinstance(value, Iterable):
            result = itemize(value)  # type: ignore
        else:
            result = str(value)
            return result
        
        return result

    if isinstance(self, dict):
        result = {k: process_value(v) for k, v in self.items()}
    elif is_dataclass(self):
        result = {
            k.name: process_value(getattr(self, k.name)) 
            for k in fields(self)
        }
    else:
        result = tuple(process_value(v) for v in self)

    return result


def make_itemizable(cls):  # decorator 
    if hasattr(cls, "itemize"):
        return cls

    func = itemize

    if is_dataclass(cls):

        @functools.wraps(itemize)
        def itemize_dataclass(self):
            result = itemize(self)
            return result

        func = itemize_dataclass

    setattr(cls, "itemize", func)
    return cls
        
