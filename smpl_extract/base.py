import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from abc import ABCMeta
from abc import abstractmethod
import enum
from typing import List
from typing import Protocol
from typing import Optional


class Printable(metaclass=ABCMeta):
    @abstractmethod
    def to_string(self) -> str: ...
    
    def display(self):
        print(self.to_string())


class Infoable(Protocol):
    def get_info(self) -> Printable: ...


class ElementTypes(enum.IntEnum):
    DirectoryEntry = enum.auto()
    SampleEntry = enum.auto()
    ProgramEntry = enum.auto()
    Sample = enum.auto()
    Program = enum.auto()


class Element(metaclass=ABCMeta):

    type_id: ElementTypes
    name: str 
    type_name: str

    def __init__(
            self, 
            path: Optional[List[str]] = None,
            parent: Optional['Element'] = None
    ) -> None:
        self._path = path or []
        self._parent = parent

    @property
    def path(self) -> List[str]:
        result = self._path
        return result

    @property
    def parent(self) -> Optional['Element']:
        result = self._parent
        return result
    
    @abstractmethod
    def get_info(self) -> Printable: ...  

        