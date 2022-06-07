import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from abc import ABCMeta
from abc import abstractmethod
import re
from typing import List
from typing import Optional
from typing import Tuple
from typing import cast

from base import Element
from base import ElementTypes
from base import Printable
from info import InfoTable
from info import InfoTree
from util.dataclass import ItemT


class ErrorNoChildWithName(Exception): ...
class ErrorNotTraversable(Exception): ...
class ErrorInvalidPath(Exception): ...


class LeafElement(Element, metaclass=ABCMeta):

    @abstractmethod
    def itemize(self) -> ItemT: ...

    def get_info(self) -> Printable:
        header = (self.name, " "*2, self.type_name)
        items = self.itemize()
        result = InfoTree(header, items)
        return result


class SampleElement(LeafElement):
    type_id = ElementTypes.SampleEntry


class ProgramElement(LeafElement):
    type_id = ElementTypes.ProgramEntry


class Traversable(Element):

    children: List[Element]
    type_id = ElementTypes.DirectoryEntry    


    def __init__(
            self,
            type_name: Optional[str] = None,
            path: Optional[List[str]] = None, 
            parent: Optional[Element] = None
    ) -> None:
        if type_name:
            self.type_name = type_name
        self.children = list()
        super().__init__(path, parent)


    def get_info(self) -> Printable:
        entries: List[Tuple[str, ...]] = []
        for child in self.children:
            name = child.name
            type_name = child.type_name
            entries.append((name, type_name))
        
        result = InfoTable(
            ("Item", "Type"),
            entries
        )
        return result


    def _sanitize_string(self, input_str: str):
        result = input_str
        return result


    _TOKENIZE_PATH_REGEX = re.compile(r"(\\{1,2}|\/)")
    def parse_path(self, path) -> Element:
        tokens_raw = self._TOKENIZE_PATH_REGEX.split(path.strip())
        tokens_raw_iter = iter(tokens_raw)

        tokens: List[str] = []
        tokens.append(next(tokens_raw_iter))
        while True:
            try:
                next(tokens_raw_iter)
                next_token = next(tokens_raw_iter)
            except StopIteration:
                break
            tokens.append(next_token)

        if len(tokens) > 0 and len(tokens[-1]) < 1:
            tokens = tokens[:-1]

        current_node = self
        for i, token in enumerate(tokens):
            token_upper = self._sanitize_string(token)

            try:
                if isinstance(current_node, Traversable):
                    current_node = cast(Traversable, current_node)
                    children = current_node.children
                    child = next((
                        x for x in children 
                        if self._sanitize_string(x.name) == token_upper
                    ))
                    if not child:
                        raise ErrorNoChildWithName()
                    current_node = child

                else:
                    raise ErrorNotTraversable

            except (ErrorNoChildWithName, ErrorNotTraversable, StopIteration):
                path_so_far = "/".join(tokens[:i]) + "/" if current_node != self else "image"
                msg = f"The entity \"{token}\" was not found in \"{path_so_far}\"."
                raise ErrorInvalidPath(msg)

        return current_node

    
    def get_samples(self) -> List[SampleElement]: 
        samples: List[SampleElement] = []
        for child in self.children:
            if child.type_id == ElementTypes.SampleEntry:
                child = cast(SampleElement, child)
                samples.append(child)
            elif isinstance(child, Traversable):
                res = child.get_samples()
                samples += res
        
        return samples

