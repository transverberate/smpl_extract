from construct.core import Adapter
from construct.core import Array
from construct.core import BuildTypes
from construct.core import ConstantOrContextLambda
from construct.core import Construct
from construct.core import Context
from construct.core import GreedyRange
from construct.core import ParsedType
from construct.core import SubconBuildTypes
from construct.core import SubconParsedType
from construct.core import Mapping
from construct.core import Subconstruct
from construct.lib.containers import Container
from construct.lib.containers import ListContainer
from enum import IntEnum
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union


def sanitize_container(container: Container)->Dict[str, Any]:
    ...


def pass_expression_deeper(expression: Any) -> Callable: 
    ...


T = TypeVar('T', bound=IntEnum)
class EnumWrapper(Generic[T], Adapter):
    def __new__(cls, subcon: Construct, mapping: Type[T])->Adapter:
        ...


U = TypeVar('U')
V = TypeVar('V')
class MappingDefault(Generic[U, V], Mapping):


    def __new__(
            cls, 
            subcon: Construct, 
            mapping: Dict[U, V],
            default: Optional[Tuple[
                Optional[Union[U, Callable[[V, Dict[V, U]], U]]],
                Optional[Union[V, Callable[[U, Dict[U, V]], V]]]
            ]] = None
    )->Mapping:
        ...


    def __init__(
            self,
            subcon,
            mapping: Dict[U, V],
            default: Optional[Tuple[
                Optional[Union[U, Callable[[V, Dict[V, U]], U]]],
                Optional[Union[V, Callable[[U, Dict[U, V]], V]]]
            ]] = None
    ):
        ...


    def _encode(self, obj: U, context, path)->V:
        ...


    def _decode(self, obj: V, context, path)->U:
        ...


def BoolConstruct(subcon)->MappingDefault:
    ...


class PaddedGeneral(
        Subconstruct[
            SubconParsedType, 
            SubconBuildTypes, 
            ParsedType, 
            BuildTypes
        ]
    ):
    def __new__(
            cls, 
            count: ConstantOrContextLambda[int],
            subcon: Construct,
            pattern: SubconBuildTypes,
            predicate: Callable[[SubconBuildTypes, Context], bool] = None
    )->Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]:
        ...


    def _default_compare(self, other: SubconBuildTypes, context: Context):
        ...


class SlicingGeneral(
        Adapter[
            SubconParsedType, 
            SubconBuildTypes,
            SubconParsedType, 
            SubconBuildTypes
        ]
    ):
    def __new__(
            cls, 
            subcon: Union[
                Array[
                    SubconParsedType,
                    SubconBuildTypes,
                    ListContainer[SubconParsedType],
                    List[SubconBuildTypes],
                ],
                GreedyRange[
                    SubconParsedType,
                    SubconBuildTypes,
                    ListContainer[SubconParsedType],
                    List[SubconBuildTypes],
                ],
            ],
            count: ConstantOrContextLambda[int],
            start: ConstantOrContextLambda[int],
            stop: ConstantOrContextLambda[int],
            step: Optional[ConstantOrContextLambda[int]] = 1,
            pattern: Optional[SubconParsedType] = None,
    )->Adapter[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]:
        ...


    def _index_compare(self, 
            other: SubconBuildTypes, 
            context: Context
    )->bool:
        ...


class SafeListConstruct(Array):
    def __new__(
            cls,
            count, 
            subcon: Construct, 
            predicate: Optional[Callable[[Any],bool]] = None
    ) -> SafeListConstruct: ...


class UnsizedConstruct(Subconstruct): ...

