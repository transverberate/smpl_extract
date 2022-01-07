import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from construct.core import Adapter
from construct.core import ConstructError
from construct.core import FixedSized
from construct.core import GreedyBytes
from construct.core import NullStripped
from construct.core import Padded
from typing import List
from typing import Union

from .data_types import CHAR_MAP_A
from .data_types import CHAR_MAP_MINUS
from .data_types import CHAR_MAP_NINE
from .data_types import CHAR_MAP_PERIOD
from .data_types import CHAR_MAP_PLUS
from .data_types import CHAR_MAP_POUND
from .data_types import CHAR_MAP_SPACE
from .data_types import CHAR_MAP_Z
from .data_types import CHAR_MAP_ZERO
from .data_types import CharFormat
from .data_types import InvalidCharacter


def _char_format_convert_byte(
        byte_in: int,
        src_fmt: CharFormat,
        dst_fmt: CharFormat
)->int:

    src_zero = CHAR_MAP_ZERO[src_fmt] 
    src_nine = CHAR_MAP_NINE[src_fmt]
    dst_zero = CHAR_MAP_ZERO[dst_fmt]
    src_A = CHAR_MAP_A[src_fmt]
    src_Z = CHAR_MAP_Z[src_fmt]
    dst_A = CHAR_MAP_A[dst_fmt]

    if src_zero <= byte_in <= src_nine:
        return dst_zero + byte_in - src_zero

    elif src_A <= byte_in <= src_Z:
        return dst_A + byte_in - src_A

    symbol_map = {
        CHAR_MAP_SPACE[src_fmt]:   CHAR_MAP_SPACE[dst_fmt],
        CHAR_MAP_POUND[src_fmt]:   CHAR_MAP_POUND[dst_fmt],
        CHAR_MAP_PLUS[src_fmt]:    CHAR_MAP_PLUS[dst_fmt],
        CHAR_MAP_MINUS[src_fmt]:   CHAR_MAP_MINUS[dst_fmt],
        CHAR_MAP_PERIOD[src_fmt]:  CHAR_MAP_PERIOD[dst_fmt],
    }

    resulting_symbol = symbol_map.get(byte_in)
    
    if resulting_symbol is None:
        raise InvalidCharacter

    return resulting_symbol


def _char_format_convert(
        bytes_in: Union[bytes, List[int]], 
        src_fmt: CharFormat,
        dst_fmt: CharFormat
)->List[int]:

    result = list(map(
        lambda x: _char_format_convert_byte(x, src_fmt, dst_fmt), 
        bytes_in
    ))
    return result


def char_ascii_to_akai(str_in: Union[str, bytes])->bytes:
    if isinstance(str_in, str):
        bytes_in = str_in.upper().encode("ascii")
    else:
        bytes_in = str_in
    result = _char_format_convert( 
        bytes_in, 
        CharFormat.ASCII, 
        CharFormat.AKAI
    )
    return bytes(result)


def _fast_akai_to_ascii_byte(byte_in: int):
    if CHAR_MAP_ZERO[CharFormat.AKAI] <= byte_in <= CHAR_MAP_NINE[CharFormat.AKAI]:
        return byte_in + CHAR_MAP_ZERO[CharFormat.ASCII] - CHAR_MAP_ZERO[CharFormat.AKAI]

    if CHAR_MAP_A[CharFormat.AKAI] <= byte_in <= CHAR_MAP_Z[CharFormat.AKAI]:
        return byte_in + CHAR_MAP_A[CharFormat.ASCII] - CHAR_MAP_A[CharFormat.AKAI]

    symbol_map = {
        CHAR_MAP_SPACE[CharFormat.AKAI]:   CHAR_MAP_SPACE[CharFormat.ASCII],
        CHAR_MAP_POUND[CharFormat.AKAI]:   CHAR_MAP_POUND[CharFormat.ASCII],
        CHAR_MAP_PLUS[CharFormat.AKAI]:    CHAR_MAP_PLUS[CharFormat.ASCII],
        CHAR_MAP_MINUS[CharFormat.AKAI]:   CHAR_MAP_MINUS[CharFormat.ASCII],
        CHAR_MAP_PERIOD[CharFormat.AKAI]:  CHAR_MAP_PERIOD[CharFormat.ASCII],
    }
    resulting_symbol = symbol_map.get(byte_in)
    
    if resulting_symbol is None:
        raise InvalidCharacter

    return resulting_symbol


def _fast_akai_to_ascii(bytes_in: Union[bytes, List[int]]):
    out_str = list()
    for byte in bytes_in:
        out_str.append(chr(_fast_akai_to_ascii_byte(byte)))
    return "".join(out_str)


def char_akai_to_ascii(bytes_in: Union[bytes, List[int]])->str:
    return _fast_akai_to_ascii(bytes_in)


class AkaiString(Adapter):
    
    def _decode(
            self, 
            obj: Union[bytes, List[int]], 
            context, 
            path
    )->str:
        del context, path  # Unused
        try:
            result = char_akai_to_ascii(obj)
        except (InvalidCharacter):
            raise ConstructError
        return result


    def _encode(
            self, 
            obj: str, 
            context, 
            path
    )->bytes:
        del context, path  # Unused
        result = char_ascii_to_akai(obj)
        return result


def AkaiPaddedString(length)->Adapter:
    result = AkaiString(FixedSized(length, Padded(
        length, 
        NullStripped(
            GreedyBytes, 
            pad=CHAR_MAP_SPACE[CharFormat.AKAI].to_bytes(1, 'little')
        ),
        pattern=CHAR_MAP_SPACE[CharFormat.AKAI].to_bytes(1, 'little')
    )))
    return result

