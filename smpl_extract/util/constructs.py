import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from typing import Generic
from typing import TypeVar
from typing import Type
from construct.core import Adapter
from construct.core import ConstructError
from construct.core import Enum as EnumConstruct



T = TypeVar('T')
class EnumWrapper(Generic[T], Adapter):

    def __init__(self, subcon, mapping: Type[T]):
        super().__init__(subcon)
        self.recast = mapping
        self.remap = EnumConstruct(subcon, mapping)

    def _decode(
            self, 
            obj, 
            context, 
            path
    )->T:
        try:
            result = self.recast(int(self.remap._decode(obj, path, context)))
        except (ValueError):
            raise ConstructError
        return result

