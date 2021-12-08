import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
from io import IOBase, SEEK_END, SEEK_SET
from construct.core import Bytes
from construct.core import Byte
from construct.core import ConstructError
from construct.core import Const
from construct.core import Int24ub
from construct.core import Struct

from util.sector import SectorStream


MDF_SECTOR_SIZE = 2352
MDF_SECTOR_HEADER_MAGIC = (
    b"\x00"
    b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
    b"\x00"
)
MDF_SECTOR_HEADER_SIZE  = 16
MDF_SECTOR_BODY_SIZE    = 2048
MDF_SECTOR_FOOTER_SIZE  = 288


MdfSectorHeaderConstruct = Struct(
    "magic" / Const(MDF_SECTOR_HEADER_MAGIC, Bytes(len(MDF_SECTOR_HEADER_MAGIC))),
    "id"    / Int24ub,
    Const(0x01, Byte)
)


MdfSectorReadConstruct = Struct(
    "header"    / MdfSectorHeaderConstruct,
    "content"   / Bytes(MDF_SECTOR_BODY_SIZE),
    "footer"    / Bytes(MDF_SECTOR_FOOTER_SIZE)
)


def is_mdf_image(stream: IOBase)->bool:
    stream_head = stream.tell()
    stream.seek(0, SEEK_SET)

    result = True
    try:
        MdfSectorHeaderConstruct.parse_stream(stream)
    except ConstructError:
        result = False 

    stream.seek(stream_head, SEEK_SET)

    return result


class MdfStream(SectorStream):


    def __init__(
            self,
            parent_stream:  IOBase,
            position:       int = 0,
            buffer_length:  int = 0x1000
    ) -> None:

        # get parent size
        offset = parent_stream.tell()
        parent_stream.seek(0, SEEK_END)
        parent_size = parent_stream.tell()
        parent_stream.seek(offset, SEEK_SET)

        num_sectors = parent_size // MDF_SECTOR_SIZE
        size = num_sectors * MDF_SECTOR_BODY_SIZE

        super().__init__(
            parent_stream, 
            size=size,
            sector_length=MDF_SECTOR_BODY_SIZE,
            position=position,
            buffer_length=buffer_length
        )

    
    def _get_address_given_sector_index(
            self, 
            sector_index: int, 
            offset: int
        ):
        sector_address  = sector_index * MDF_SECTOR_SIZE
        
        mdf_address = sector_address + MDF_SECTOR_HEADER_SIZE + offset
        return mdf_address

