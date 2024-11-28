from collections.abc import Iterable
from construct.lib.containers import Container
from dataclasses import fields
from dataclasses import is_dataclass
from io import IOBase
from typing import Any 
from typing import Protocol
from typing import Dict
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import Union

from .constructs import sanitize_container


ItemT = Union[Mapping[str, 'ItemT'], Tuple['ItemT', ...], str]


class Itemizable(Protocol):
    def itemize(self) -> ItemT: ...


def process_value(value)->Union[str, ItemT]:
    result: Union[str, ItemT]
    if hasattr(value, "itemize"):
        result = value.itemize()
    elif is_dataclass(value):
        result = itemize_general(value)
    elif not isinstance(value, str) and not isinstance(value, IOBase) \
            and isinstance(value, Iterable):

        result = itemize_general(value)  # type: ignore
    else:
        result = str(value)
        return result
    
    return result


def itemize_general(self: Union[Sequence[Any], Dict[str, Any]])->ItemT:
    if isinstance(self, Container):
        sanitized = sanitize_container(self)
        result = {
            k: process_value(v) for k, v in sanitized.items()
        }
    elif isinstance(self, dict):
        result = {
            k: process_value(v) for k, v in self.items()
        }
    elif is_dataclass(self):
        result = {
            k.name: process_value(getattr(self, k.name))
            for k in fields(self)
        }
    else:
        result = tuple(process_value(v) for v in self)
    return result


def get_common_field_args(common_dataclass: Any, source_instance):
    result = {
        k.name: getattr(source_instance, k.name)
        for k in fields(common_dataclass)
    }
    return result

