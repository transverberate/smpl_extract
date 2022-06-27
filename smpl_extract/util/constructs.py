import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct.core import Adapter
from construct.core import Array
from construct.core import ConstructError
from construct.core import Enum as EnumConstruct
from construct.core import evaluate
from construct.core import Filter
from construct.core import Mapping
from construct.core import MappingError
from construct.core import RangeError
from construct.core import Slicing
from construct.core import Subconstruct
from construct.core import Sequence
from construct.lib.containers import Container
from enum import IntEnum
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Type

from base import Element


def sanitize_container(container: Container)->Dict[str, Any]:
    result = {
        k : v for k, v in container.items() 
        if len(k)>0 and k[0] != "_"
    }
    return result


def pass_expression_deeper(expression: Any) -> Callable:
    if callable(expression):
        new_expression = lambda this: expression(this._)
    else:
        new_expression = lambda this: expression
        
    return new_expression


def wrap_context_parent(
    f_realize: Callable,
    context: Container,
    parent: Element
) -> Callable:


    def wrap_realize():
        context.parent = parent  # type: ignore
        realize_result = f_realize()
        return realize_result
    

    result = wrap_realize
    return result


T = TypeVar('T', bound=IntEnum)
class EnumWrapper(Generic[T], Adapter):


    def __init__(self, subcon, mapping: Type[T]):
        super().__init__(subcon)  # type: ignore
        self.recast = mapping
        self.remap = EnumConstruct(subcon, mapping)


    def _decode(self, obj, context, path)->T:
        try:
            result = self.recast(int(self.remap._decode(obj, path, context)))
        except ValueError:
            raise ConstructError from ValueError
        return result


class MappingDefault(Mapping):


    def __init__(
            self,
            subcon,
            mapping: Dict,
            default = None
    ):
        super().__init__(subcon, mapping)  # type: ignore
        default = default or (None, None)
        self.default_decode, self.default_encode = default


    def _encode(self, obj, context, path):
        try:
            result = super()._encode(obj, context, path)
        except MappingError as e:
            if self.default_encode is None:
                raise e
            result = self.default_encode
            if callable(result):
                result = result(obj, self.encmapping)  # type: ignore
        return result

    
    def _decode(self, obj, context, path):
        try:
            result = super()._decode(obj, context, path)
        except MappingError as e:
            if self.default_decode is None:
                raise e
            result = self.default_decode
            if callable(result):
                result = result(obj, self.decmapping)  # type: ignore
        return result


def BoolConstruct(subcon):
    result = MappingDefault(subcon, {False: 0}, (True, 1))  # type: ignore
    return result 


class PaddedGeneral(Subconstruct):
    def __init__(self, 
            count,
            subcon,
            pattern,
            predicate = None
    ) -> None:
        super().__init__(subcon)  # type: ignore
        self.count = count 
        self.pattern = pattern 
        self.predicate = predicate or self._default_compare

    
    def _default_compare(self, other, context):
        del context  # Unused
        def filter_container(obj):
            result_inner = sanitize_container(obj)
            return result_inner
        first = filter_container(self.pattern)
        second = filter_container(other)
        result = first == second 
        return result


    def _parse(self, stream, context, path):
        desired_count = evaluate(self.count, context)
        filtered_construct = Filter(
            self.predicate,
            Array(desired_count, self.subcon)
        )
        contents = filtered_construct._parse(stream, context, path)  # type: ignore
        result = contents
        return result

    
    def _build(self, obj, stream, context, path):
        desired_count = evaluate(self.count, context)
        actual_count = len(obj)
        diff_count = desired_count - actual_count
        if not 0 <= diff_count:
            raise RangeError(f"expected {desired_count} elements, found {actual_count}", path=path)
        padding_content = (self.pattern,)*diff_count 
        actual_content = tuple(x for x in obj)
        comb_content = (actual_content, padding_content)
        comb_construct = Sequence(
            Array(actual_count, self.subcon),
            Array(diff_count, self.subcon)
        )
        result = comb_construct._build(comb_content, stream, context, path)
        return result


    def _sizeof(self, context, path):
        desired_count = evaluate(self.count, context)
        comb_construct = Array(desired_count, self.subcon)
        result = comb_construct._sizeof(context, path)  # type: ignore
        return result


class SlicingGeneral(Adapter):


    def __init__(
            self,
            subcon,
            count,
            start,
            stop,
            step = 1,
            pattern = None
    )->None:
        super().__init__(subcon)  # type: ignore
        self.count = count
        self.start = start
        self.stop = stop
        self.step = step 
        self.pattern = pattern

    
    def _realize(self, 
            context
    )->Tuple[Slicing, int, int, int]:
        count = evaluate(self.count, context)
        start = evaluate(self.start, context)
        stop = evaluate(self.stop, context)
        step = evaluate(self.step, context)

        result = Slicing(
            self.subcon,  # type: ignore
            count,
            start,
            stop,
            step,
            self.pattern
        )
        return result, start, stop, step


    def _decode(self, obj, context, path):
        slicing = self._realize(context)[0]
        result = slicing._decode(obj, context, path)
        return result


    def _encode(self, obj, context, path):
        slicing, start, stop, step = self._realize(context)
        result = slicing._encode(obj[start:stop:step], context, path)
        return result


class SafeListConstruct(Array):


    def __init__(
            self, 
            count, 
            subcon, 
            predicate: Optional[Callable[[Any],bool]] = None
    ) -> None:
        super().__init__(count, subcon)  # type: ignore
        self.predicate = predicate


    def _parse(self, stream, context, path):
        count = evaluate(self.count, context)
        if count <= 0:
            raise RangeError(f"invalid count {count}", path=path)
        obj = dict()
        if self.predicate is not None:
            predicate = self.predicate
        else:
            predicate = lambda obj: True
        for i in range(count):
            context._index = i
            try:
                entry = self.subcon._parsereport(stream, context, path)  # type: ignore
            except (UnicodeDecodeError, ConstructError, KeyError, IndexError) as e:
                continue
            if predicate(obj):
                obj[i] = (entry)
        return obj


class UnsizedConstruct(Subconstruct):


    def _sizeof(self, context, path) -> int:
        try:
            return super()._sizeof(context, path)  # type: ignore
        except:
            return 0  # really bad practice 

