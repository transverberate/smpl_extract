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
    SampleGeneralized = enum.auto()
    ProgramGeneralized = enum.auto()


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
        self._safe_name: Optional[str] = None
        self._export_name: Optional[str] = None

    @property
    def path(self) -> List[str]:
        if hasattr(self, "_path"):
            result = self._path
        else:
            result = []
        return result

    @property
    def parent(self) -> Optional['Element']:
        if hasattr(self, "_parent"):
            result = self._parent
        else:
            result = None
        return result

    @property
    def safe_name(self) -> str:
        result = self.name
        if hasattr(self, "_safe_name"):
            if self._safe_name is not None:
                result = self._safe_name
        return result

    @property
    def export_name(self) -> str:
        result = self.name
        if hasattr(self, "_export_name"):
            if self._export_name is not None:
                result = self._export_name
        return result

    def export_path(self) -> List[str]:
        current_path = self.path
        if len(current_path) <= 0:
            return []
        new_path = []
        current_node = self
        while current_node is not None and len(current_node.path) > 0:
            new_path = [current_node.export_name] + new_path
            current_node = current_node.parent
        return new_path
    
    @abstractmethod
    def get_info(self) -> Printable: ...  

