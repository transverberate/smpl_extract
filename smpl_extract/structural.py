import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from abc import ABCMeta
from abc import abstractmethod
import os
import re
from typing import Callable
from typing import cast
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

from base import Element
from base import ElementTypes
from base import Printable
from elements import LeafElement
from generalized.sample import Sample
from generalized.wav import export_wav
from info import InfoTable


class ErrorNoChildWithName(Exception): ...
class ErrorNotTraversable(Exception): ...
class ErrorInvalidPath(Exception): ...
class ErrorInvalidName(Exception): ...


_T_ROUTINE = Callable[[List[Element]],List[Element]]


class SampleElement(LeafElement, metaclass=ABCMeta):
    type_id = ElementTypes.SampleEntry

    @abstractmethod
    def to_generalized(self) -> Sample: ...


class ProgramElement(LeafElement):
    type_id = ElementTypes.ProgramEntry


class ExportManager:
    def __init__(
            self,
            output_directory: str = "",
            routines: Optional[Dict[
                str, 
                Callable[[List[Sample]],List[Sample]]
            ]] = None
        ) -> None:
        self.output_directory: str
        self.routines: Dict[str, Callable[[List[Sample]],List[Sample]]]
        self.samples: List[Sample]
        self.level: Tuple[str, ...]

        self.output_directory = output_directory
        self.routines = routines or {}
        self.samples = []
        self.level = ()


    def add_sample(self, sample: Sample):
        self.samples.append(sample)


    def set_level(self, level: Tuple[str, ...]):
        self.level = level
        self.samples.clear()

    
    def finish_level(self):
        self.export_samples()
        self.level = ()


    _SAFE_ENDING = re.compile(r"(.+?)\s*\.?\s*$")
    _INVALID_FILE_NAME = re.compile(r"[^\w\-. ]+")
    def sanitize_name(self, name: str, is_file=True)->str:
        result = self._INVALID_FILE_NAME.sub(" ", name).strip()
        match = self._SAFE_ENDING.match(result)
        if match:
            result = match.group(1)
        if len(result) <= 0:
            result = "0"
        if is_file:
            match = re.match(r"\w", result)
            if not match:
                result = "0" + result
        return result


    def make_output_path(self, sample_name: str) -> str:
        components = list(self.level) + [sample_name]
        components_safe = [self.sanitize_name(x, False) for x in components[:-1]]
        components_safe += [self.sanitize_name(components[-1], True)]
        result = "/".join(components_safe)
        return result


    def export_samples(self):
        samples = self.samples
        for f_routine in self.routines.values():
            samples = f_routine(samples)

        for sample in samples:
            inner_path = self.make_output_path(sample.name)
            total_path = os.path.join(self.output_directory, inner_path) + ".wav"
            dir_name = os.path.dirname(total_path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            export_wav(sample, total_path)
            print(f"Exported {inner_path}.wav")

        self.samples.clear()
        return 


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
            name = child.safe_name
            type_name = child.type_name
            entries.append((name, type_name))
        
        result = InfoTable(
            ("Item", "Type"),
            entries
        )
        return result


    def _sanitize_string(self, input_str: str):
        result = input_str.strip()
        return result


    _TOKENIZE_PATH_REGEX = re.compile(r"(\\{1,2}|\/)")
    def parse_path(
            self, 
            path, 
            routines: Optional[Dict[str, _T_ROUTINE]] = None
    ) -> Element:

        f_make_safe_names = lambda x: x
        if routines is not None:
            f_make_safe_names = routines.get("make_safe_names", lambda x: x)

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
                    children = f_make_safe_names(children)

                    child = next((
                        x for x in children 
                        if self._sanitize_string(x.safe_name) == token_upper
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

    
    def export_samples(self, export_manager: ExportManager):
        
        export_manager.set_level(tuple(self.path))
        for child in self.children:
            if child.type_id == ElementTypes.SampleEntry:
                child = cast(SampleElement, child)
                sample = child.to_generalized()
                export_manager.add_sample(sample)
            elif isinstance(child, Traversable):
                child.export_samples(export_manager)
        
        export_manager.finish_level()
        return


_T = TypeVar("_T", bound=Element)
class Image(Traversable):


    _path: ClassVar = []
    _parent: ClassVar = None


    def combine_stereo_routine(
            self, 
            samples: List[Sample]
    ) -> List[Sample]:
        result = samples
        return result


    def make_safe_names_routine(
            self, 
            samples: List[_T]
    ) -> List[_T]:
        result = samples
        return result


    def make_export_names_routine(self, samples: List[_T]) -> List[_T]:
        result = samples
        return result

