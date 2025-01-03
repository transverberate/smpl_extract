from abc import ABCMeta
from abc import abstractmethod
import os
import re
from typing import Any
from typing import Callable
from typing import cast
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

from smpl_extract.base import Element
from smpl_extract.base import ElementTypes
from smpl_extract.base import Printable
from smpl_extract.elements import LeafElement
from smpl_extract.generalized.sample import combine_stereo
from smpl_extract.generalized.sample import Sample
from smpl_extract.generalized.wav import export_wav
from smpl_extract.info import InfoTable


class ErrorNoChildWithName(Exception): ...
class ErrorNotTraversable(Exception): ...
class ErrorInvalidPath(Exception): ...
class ErrorInvalidName(Exception): ...
class CouldNotDetermineName(Exception): ...


T_ROUTINE = Callable[[List[Element]], List[Element]]
T_SAMPLE_ROUTINE = Callable[[List[Sample]],List[Sample]]


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
                T_SAMPLE_ROUTINE
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


    def make_output_path(self, sample: Sample) -> str:
        components = sample.export_path()
        result = "/".join(components)
        return result


    def export_samples(self):
        samples = self.samples
        for f_routine in self.routines.values():
            samples = f_routine(samples)

        for sample in samples:
            inner_path = self.make_output_path(sample)
            total_path = os.path.join(self.output_directory, inner_path) + ".wav"
            dir_name = os.path.dirname(total_path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            export_wav(sample, total_path)
            print(f"Exported {inner_path}.wav")

        self.samples.clear()
        return 


_T_CHILD = TypeVar("_T_CHILD", bound=Element)
class Traversable(Element, Generic[_T_CHILD]):

    type_id = ElementTypes.DirectoryEntry    


    def __init__(
            self,
            f_realize_children: Callable[
                [Dict[str, Any]], 
                List[_T_CHILD]
            ],
            routines: Optional[Dict[str, T_ROUTINE]] = None,
            path: Optional[List[str]] = None, 
            parent: Optional[Element] = None,
            type_name: Optional[str] = None,
    ) -> None:
        super().__init__(path, parent)
        if type_name:
            self.type_name = type_name
        self._f_realize_children = f_realize_children
        self._routines: Dict[str, T_ROUTINE] = routines or {}
        self._children = None


    @property
    def children(self) -> List[_T_CHILD]:
        if self._children is None:
            context_additions = {
                "_elem_parent": self,
                "_elem_routines": self._routines
            }
            children = self._f_realize_children(context_additions)
            for routine in self._routines.values():
                children = routine(children)  # type: ignore
            self._children = children
        return self._children  # type: ignore


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

    
    def set_routines(self, routines: Dict[str, T_ROUTINE]):
        self._routines = routines


    def _sanitize_string(self, input_str: str):
        result = input_str.strip()
        return result


    _TOKENIZE_PATH_REGEX = re.compile(r"(\\{1,2}|\/)")
    def parse_path(
            self, 
            path
    ) -> Element:

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
            token_sanitized = self._sanitize_string(token)

            try:
                if isinstance(current_node, Traversable):
                    current_node = cast(Traversable, current_node)
                    children = current_node.children

                    child = next((
                        x for x in children 
                        if self._sanitize_string(x.safe_name) == token_sanitized
                    ))
                    if not child:
                        raise ErrorNoChildWithName()
                    current_node = child

                else:
                    raise ErrorNotTraversable

            except (ErrorNoChildWithName, ErrorNotTraversable, StopIteration) as e:
                path_so_far = "/".join(tokens[:i]) + "/" if current_node != self else "image"
                msg = f"The entity \"{token}\" was not found in \"{path_so_far}\"."
                raise ErrorInvalidPath(msg)

        if isinstance(current_node, Traversable):
            children = current_node.children

        return current_node

    
    def export_samples(
            self, 
            export_manager: ExportManager
    ):
        export_manager.set_level(tuple(self.path))
        children = self.children

        for child in children:
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
        sample_dict = {s.export_name: s for s in samples}
        marked = {n: False for n in sample_dict}
        result = []
        for sample in samples:

            result_sample = sample
            name = sample.export_name
            if marked[name]:
                continue

            match = self._STEREO_FILENAME.match(name)
            if match:
                alternate_ending = "R" if match.group(3) == "L" else "L"
                alternate_name = "".join((
                    match.group(1), 
                    match.group(2), 
                    alternate_ending
                ))
                if alternate_name in sample_dict.keys():
                    alternate_sample = sample_dict[alternate_name]
                    alternate_sample = cast(Sample, alternate_sample)
                    if alternate_ending == "R":
                        pairs = [sample, alternate_sample]
                    else:
                        pairs = [alternate_sample, sample]

                    new_name = match.group(1)
                    result_sample = combine_stereo(pairs[0], pairs[1], new_name)
                    marked[alternate_name] = True
                
            result.append(result_sample)
            marked[name] = True

        return result


    _INVALID_CHARS_REMOVE = re.compile(r"[\'\"\`]+")
    _INVALID_CHARS_REPLACE = re.compile(r"([^\w\-=\:.@#&+ ]+|(?<!\w)\:+)")
    def make_safe_name(self, name, is_file=True) -> str:
        del is_file
        safe_name = self._INVALID_CHARS_REMOVE.sub("", name)
        safe_name = self._INVALID_CHARS_REPLACE.sub(" ", safe_name)
        safe_name = safe_name.strip()
        return safe_name


    _SAFE_ENDING = re.compile(r"(.+?)\s*\.?\s*$")
    _INVALID_FILE_NAME = re.compile(r"[^\w\-\.# ]+")
    def make_export_name(self, name, is_file=True) -> str:
        export_name = self.make_safe_name(name)
        export_name = self._INVALID_FILE_NAME.sub(" ", name).strip()
        match = self._SAFE_ENDING.match(export_name)
        if match:
            export_name = match.group(1)
        if len(export_name) <= 0:
            export_name = "0"
        match = re.match(r"\w", export_name)
        if not match:
            export_name = "0" + export_name
        if not is_file:
            if export_name[-1] in (".", "-"):
                export_name = export_name + "0"
        return export_name


    _STEREO_FILENAME = re.compile(r"(.*?)([\s-]+)(L|R)\s*$")
    def _add_count_to_name(self, name: str, count: int) -> str:
        count_str = "(" + str(count) + ")"
        delim = " "
        tokens = [name, count_str]
        match = self._STEREO_FILENAME.match(name)
        if match:
            tokens = [
                match.group(1),
                count_str,
                match.group(3)
            ]
        new_name = delim.join(tokens)
        return new_name


    def sanitize_names_general(
            self, 
            elements: List[_T],
            f_sanitize: Callable[[str, bool], str],
            f_set: Callable[[_T, str], None]
    ) -> List[_T]:
        candidate_names: Dict[str, List[_T]] = {}
        for element in elements:
            is_file = element.type_id != ElementTypes.DirectoryEntry
            candidate_name = f_sanitize(element.name, is_file)

            if candidate_name not in candidate_names.keys():
                candidate_names[candidate_name] = []
            candidate_names[candidate_name].append(element)

        for name, subelements in candidate_names.items():
            if len(subelements) == 1:
                element = subelements[0]
                f_set(element, name)
                continue
            
            i = 0
            for element in subelements:
                i += 1
                if i > 1:
                    next_name = self._add_count_to_name(name, i)
                    j = 0
                    while (next_name in candidate_names.keys()):
                        i += 1
                        j += 1
                        next_name = self._add_count_to_name(name, i)
                        if j > len(candidate_names.keys()):
                            # This should never(?) happen
                            raise CouldNotDetermineName(
                                "Unable to determine proper (sanitized) "
                                f"name for {element.name}. Too many name "
                                "collisions."
                            )
                else:
                    next_name = name
                f_set(element, next_name)

        result = elements
        return result


    def make_safe_names_routine(
            self, 
            elements: List[_T]
    ) -> List[_T]:
        result = self.sanitize_names_general(
            elements,
            self.make_safe_name,
            lambda element, name: setattr(element, "_safe_name", name)
        )
        return result


    def make_export_names_routine(self, elements: List[_T]) -> List[_T]:
        result = self.sanitize_names_general(
            elements,
            self.make_export_name,
            lambda element, name: setattr(element, "_export_name", name)
        )
        return result

