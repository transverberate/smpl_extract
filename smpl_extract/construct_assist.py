from abc import abstractmethod
from typing import Any, Dict
from construct.core import Construct


class ConstructAssist:

    def __init__(
        self,
        construct: Construct
    ) -> None:
        self._construct = construct

    
    @abstractmethod
    def get_dict(self)->Dict[str, Any]:
        raise NotImplemented


    def sizeof(self):
        return self._construct.sizeof(**self.get_dict())


    def build(self)->bytes:
        result = self._construct.build(self.get_dict())
        return result

    
    def build_file(self, filename: str):
        result = self._construct.build_file(
            self.get_dict(), 
            filename
        )
        return result

    
    def build_stream(self, stream):
        result = self._construct.build_stream(
            self.get_dict(), 
            stream
        )
        return result