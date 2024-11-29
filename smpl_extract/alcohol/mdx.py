from construct.core import Bytes
from construct.core import ConstructError
from construct.core import Const
from construct import Default
from construct.core import ExprValidator
from construct.core import Int64ul
from construct.core import Padding
from construct.core import Struct
from construct.expr import obj_
from io import IOBase
from io import SEEK_SET

from smpl_extract.util.stream import StreamOffset


MDX_SECTOR_HEADER_MAGIC = (
    b"MEDIA\x20DESCRIPTOR"
)


MdxHeaderConstruct = Struct(
    "magic" / Const(MDX_SECTOR_HEADER_MAGIC, Bytes(len(MDX_SECTOR_HEADER_MAGIC))),
    "version" / Default(Bytes(2), b"\x02\x01"),
    "copyright" / ExprValidator(
        Default(Bytes(26), b"\x20"*26),
        obj_[0] == 0xA9  # type: ignore
    ),
    Padding(4, b"\xFF"),
    "eof" / Int64ul,
    Padding(8)
)


def is_mdx_image(stream: IOBase)->bool:
    stream_head = stream.tell()
    stream.seek(0, SEEK_SET)

    result = True
    try:
        MdxHeaderConstruct.parse_stream(stream)  # type: ignore
    except ConstructError as e:
        result = False 

    stream.seek(stream_head, SEEK_SET)

    return result


def MdxStream(
        parent_stream: IOBase, 
        position: int = 0, 
        buffer_length: int = 0x1000
    ):
    header = MdxHeaderConstruct.parse_stream(parent_stream)  # type: ignore
    offset = MdxHeaderConstruct.sizeof()
    size = header.eof - offset
    result = StreamOffset(
        parent_stream, 
        size, 
        offset, 
        position=position, 
        buffer_length=buffer_length
    )
    return result
    
