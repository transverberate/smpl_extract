import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
import enum 
from enum import Enum
from typing import Dict, List, Protocol, Tuple, Union
from construct.core import Struct,  Bytes, Padding, Int16ul, Int8ul, Int24ul, Int8sl, Int32ul, ExprAdapter

from midi import MidiNote


AKAI_SECTOR_SIZE = 0x2000

S1000_VOLUME_TYPE = 1
S3000_VOLUME_TYPE = 3

FILE_TABLE_END_FLAG = 0xD747

AKAI_SAMPLE_DATA_OFFSET_S1000 = 0x96
AKAI_SAMPLE_WORDLENGTH = 0x02


# Character Encoding 


class InvalidCharacter(Exception):
    pass

class CharFormat(Enum):
    ASCII   = enum.auto()
    AKAI    = enum.auto()


_CHAR_MAP_ZERO      = { CharFormat.ASCII: ord("0"),  CharFormat.AKAI: 0x00 }
_CHAR_MAP_NINE      = { CharFormat.ASCII: ord("9"),  CharFormat.AKAI: 0x09 }
_CHAR_MAP_SPACE     = { CharFormat.ASCII: ord(" "),  CharFormat.AKAI: 0x0A }
_CHAR_MAP_A         = { CharFormat.ASCII: ord("A"),  CharFormat.AKAI: 0x0B }
_CHAR_MAP_Z         = { CharFormat.ASCII: ord("Z"),  CharFormat.AKAI: 0x24 }
_CHAR_MAP_POUND     = { CharFormat.ASCII: ord("#"),  CharFormat.AKAI: 0x25 }
_CHAR_MAP_PLUS      = { CharFormat.ASCII: ord("+"),  CharFormat.AKAI: 0x26 }
_CHAR_MAP_MINUS     = { CharFormat.ASCII: ord("-"),  CharFormat.AKAI: 0x27 }
_CHAR_MAP_PERIOD    = { CharFormat.ASCII: ord("."),  CharFormat.AKAI: 0x28 }


def _char_format_convert_byte(
        byte_in: int,
        src_fmt: CharFormat,
        dst_fmt: CharFormat
)->int:

    src_zero = _CHAR_MAP_ZERO[src_fmt] 
    src_nine = _CHAR_MAP_NINE[src_fmt]
    dst_zero = _CHAR_MAP_ZERO[dst_fmt]
    src_A = _CHAR_MAP_A[src_fmt]
    src_Z = _CHAR_MAP_Z[src_fmt]
    dst_A = _CHAR_MAP_A[dst_fmt]

    if src_zero <= byte_in <= src_nine:
        return dst_zero + byte_in - src_zero

    elif src_A <= byte_in <= src_Z:
        return dst_A + byte_in - src_A

    symbol_map = {
        _CHAR_MAP_SPACE[src_fmt]:   _CHAR_MAP_SPACE[dst_fmt],
        _CHAR_MAP_POUND[src_fmt]:   _CHAR_MAP_POUND[dst_fmt],
        _CHAR_MAP_PLUS[src_fmt]:    _CHAR_MAP_PLUS[dst_fmt],
        _CHAR_MAP_MINUS[src_fmt]:   _CHAR_MAP_MINUS[dst_fmt],
        _CHAR_MAP_PERIOD[src_fmt]:  _CHAR_MAP_PERIOD[dst_fmt],
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
    if _CHAR_MAP_ZERO[CharFormat.AKAI] <= byte_in <= _CHAR_MAP_NINE[CharFormat.AKAI]:
        return byte_in + _CHAR_MAP_ZERO[CharFormat.ASCII] - _CHAR_MAP_ZERO[CharFormat.AKAI]

    if _CHAR_MAP_A[CharFormat.AKAI] <= byte_in <= _CHAR_MAP_Z[CharFormat.AKAI]:
        return byte_in + _CHAR_MAP_A[CharFormat.ASCII] - _CHAR_MAP_A[CharFormat.AKAI]

    symbol_map = {
        _CHAR_MAP_SPACE[CharFormat.AKAI]:   _CHAR_MAP_SPACE[CharFormat.ASCII],
        _CHAR_MAP_POUND[CharFormat.AKAI]:   _CHAR_MAP_POUND[CharFormat.ASCII],
        _CHAR_MAP_PLUS[CharFormat.AKAI]:    _CHAR_MAP_PLUS[CharFormat.ASCII],
        _CHAR_MAP_MINUS[CharFormat.AKAI]:   _CHAR_MAP_MINUS[CharFormat.ASCII],
        _CHAR_MAP_PERIOD[CharFormat.AKAI]:  _CHAR_MAP_PERIOD[CharFormat.ASCII],
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
    # result = _char_format_convert( 
    #     bytes_in, 
    #     CharFormat.AKAI,
    #     CharFormat.ASCII
    # )
    
    # return bytes(result).decode("ascii")



def rpad_bytes(in_bytes: bytes, size: int, delim: bytes = b'\0'):
    n = len(in_bytes)
    diff = size - n
    adj_diff = diff if diff > 0 else 0
    result = in_bytes + delim*adj_diff
    return result[:size]


# Data Types


class VolumeType(Enum):
    INACTIVE        = enum.auto()
    VOLUME_S1000    = enum.auto()
    VOLUME_S3000    = enum.auto()
    UNKNOWN         = enum.auto()
    @classmethod
    def from_int(cls, int_in: int):
        mapping = {
            0x00:   cls.INACTIVE,
            0x01:   cls.VOLUME_S1000,
            0x03:   cls.VOLUME_S3000
        }
        result = mapping.get(int_in, cls.UNKNOWN)
        return result
    def to_int(self):
        mapping = {
            self.INACTIVE:      0x00,
            self.VOLUME_S1000:  0x01,
            self.VOLUME_S3000:  0x03
        }
        return mapping.get(self, 0x00)
    def to_string(self):
        mapping = {
            self.INACTIVE:      "Inactive Volume",
            self.VOLUME_S1000:  "S1000 Volume",
            self.VOLUME_S3000:  "S3000 Volume"
        }
        return mapping.get(self, "Unknown")


class FileType(Enum):
    UNKOWN          = enum.auto()
    DRUM            = enum.auto()
    PROGRAM_S1000   = enum.auto()
    QL              = enum.auto()
    SAMPLE_S1000    = enum.auto()
    EFFECT          = enum.auto()
    PROGRAM_S3000   = enum.auto()
    SAMPLE_S3000    = enum.auto()
    @classmethod
    def from_byte(cls, int_in: int):
        mapping = {
            0x64:   cls.DRUM,
            0x70:   cls.PROGRAM_S1000,
            0x71:   cls.QL,
            0x73:   cls.SAMPLE_S1000,
            0x78:   cls.EFFECT,
            0xf0:   cls.PROGRAM_S3000,
            0xf3:   cls.SAMPLE_S3000
        }
        result = mapping.get(int_in, cls.UNKOWN)
        return result
    def to_byte(self):
        mapping = {
            self.DRUM:           0x64,
            self.PROGRAM_S1000:  0x70,
            self.QL:             0x71,
            self.SAMPLE_S1000:   0x73,
            self.EFFECT:         0x78,
            self.PROGRAM_S3000:  0xf0,
            self.SAMPLE_S3000:   0xf3
        }
        return mapping.get(self, 0x00)
    def to_string(self):
        mapping = {
            self.DRUM:           "Drum",
            self.PROGRAM_S1000:  "S1000 Program",
            self.QL:             "QL",
            self.SAMPLE_S1000:   "S1000 Sample",
            self.EFFECT:         "Effect",
            self.PROGRAM_S3000:  "S3000 Program",
            self.SAMPLE_S3000:   "S3000 Sample"
        }
        return mapping.get(self, "Unknown")


class SampleType(Enum):
    UNKOWN  = enum.auto()
    S1000   = enum.auto()
    S3000   = enum.auto()
    @classmethod
    def from_byte(cls, int_in: int):
        mapping = {
            0x01:   cls.S1000,
            0x03:   cls.S3000
        }
        result = mapping.get(int_in, cls.UNKOWN)
        return result
    def to_byte(self):
        mapping = {
            self.S1000: 0x01,
            self.S3000: 0x03
        }
        return mapping.get(self, 0x00)
    def to_string(self):
        mapping = {
            self.S1000: "S1000 Sample",
            self.S3000: "S3000 Sample"
        }
        return mapping.get(self, "Unknown")


class AkaiLoopType(Enum):
    UNKOWN              = enum.auto()
    LOOP_IN_RELEASE     = enum.auto()
    LOOP_UNTIL_RELEASE  = enum.auto()
    LOOP_INACTIVE       = enum.auto()
    PLAY_TO_SAMPLE_END  = enum.auto()
    @classmethod
    def from_byte(cls, int_in: int):
        mapping = {
            0x00:   cls.LOOP_IN_RELEASE,
            0x01:   cls.LOOP_UNTIL_RELEASE,
            0x02:   cls.LOOP_INACTIVE,
            0x03:   cls.PLAY_TO_SAMPLE_END
        }
        result = mapping.get(int_in, cls.UNKOWN)
        return result
    def to_byte(self):
        mapping = {
            self.LOOP_IN_RELEASE:       0x00,
            self.LOOP_UNTIL_RELEASE:    0x01,
            self.LOOP_INACTIVE:         0x02,
            self.PLAY_TO_SAMPLE_END:    0x03
        }
        return mapping.get(self, 0xFF)
    def to_string(self):
        mapping = {
            self.LOOP_IN_RELEASE:       "Loop in release",
            self.LOOP_UNTIL_RELEASE:    "Loop until release",
            self.LOOP_INACTIVE:         "No loop",
            self.PLAY_TO_SAMPLE_END:    "Play until end"
        }
        return mapping.get(self, "Unknown")

# Data Structures


VolumeEntryConstruct = Struct(
    "name" / ExprAdapter(
        Bytes(12), 
        lambda x, y: char_akai_to_ascii(x).strip(), 
        lambda x, y: rpad_bytes(
            char_ascii_to_akai(x), 
            12, 
            bytes([_CHAR_MAP_SPACE[CharFormat.AKAI]])
        )
    ),
    "type" / ExprAdapter(
        Int16ul, 
        lambda x, y: VolumeType.from_int(x), 
        lambda x, y: VolumeType.to_int(x),
    ),
    "start" / Int16ul
).compile()


VolumeEntriesConstruct = Struct(
    "volume_entries" / VolumeEntryConstruct[100]
).compile()


PartitionHeaderConstruct = Struct(
    "size" / Int16ul,
    Padding(200)
).compile()


SegmentAllocationTableConstruct = Struct(
    "fat" / Int16ul[11386]
).compile()


FileEntryConstruct = Struct(
    "name" / ExprAdapter(
        Bytes(12), 
        lambda x, y: char_akai_to_ascii(x).strip(), 
        lambda x, y: rpad_bytes(
            char_ascii_to_akai(x), 
            12, 
            bytes([_CHAR_MAP_SPACE[CharFormat.AKAI]])
        )
    ),
    Padding(4),
    "type" / ExprAdapter(
        Int8ul, 
        lambda x, y: FileType.from_byte(x), 
        lambda x, y: FileType.to_byte(x),
    ),
    "size" / Int24ul,
    "start" / Int16ul,
    Padding(2)
).compile()


LoopDataConstruct = Struct(
    "loop_start" / Int32ul,
    "loop_length_fine" / Int16ul,
    "loop_length_coarse" / Int32ul,
    "loop_duration" / Int16ul
).compile()


SampleHeaderConstruct = Struct(
    "id" / ExprAdapter(
        Int8ul, 
        lambda x, y: SampleType.from_byte(x),
        lambda x, y: SampleType.to_byte(x)
    ),
    Padding(1),
    "note_pitch" / ExprAdapter(
        Int8ul, 
        lambda x, y: MidiNote.from_akai_byte(x),
        lambda x, y: MidiNote.to_akai_byte(x)
    ),
    "name" / ExprAdapter(
        Bytes(12), 
        lambda x, y: char_akai_to_ascii(x).strip(), 
        lambda x, y: rpad_bytes(
            char_ascii_to_akai(x), 
            12, 
            bytes([_CHAR_MAP_SPACE[CharFormat.AKAI]])
        )
    ),
    Padding(4),
    "loop_type" / ExprAdapter(
        Int8ul, 
        lambda x, y: AkaiLoopType.from_byte(x),
        lambda x, y: AkaiLoopType.to_byte(x)
    ),
    "pitch_offset_cents" / ExprAdapter(
        Int8sl, 
        lambda x, y: round(x * 50/0x7F),
        lambda x, y: round(x * 0x7F/50)
    ),
    "pitch_offset_semi" / ExprAdapter(
        Int8sl, 
        lambda x, y: round(x * 50/0x7F),
        lambda x, y: round(x * 0x7F/50)
    ),
    Padding(4),
    "samples_cnt" / Int32ul,
    "play_start" / Int32ul,
    "play_end" / Int32ul,
    "loop_data_table" / LoopDataConstruct[8],
    Padding(4),
    "sampling_rate" / Int16ul
).compile()


# if __name__ == "__main__":
#     VOLUME_ENTRY_STRUCT.compile(filename=os.path.join(_SCRIPT_PATH, "structs/volume_entry.py"))
#     VOLUME_ENTRIES_STRUCT.compile(filename="structs/volume_entry_table.py")
#     PARTITION_HEADER_STRUCT.compile(filename="structs/partition_header.py")
#     FAT_STRUCT.compile(filename="structs/fat_struct.py")
#     FILE_ENTRY_STRUCT.compile(filename="structs/file_entry.py")
#     LOOP_DATA_STRUCT.compile("structs/loop_data.py")
#     SAMPLE_HEADER_STRUCT.compile("structs/sample_header.py")