import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from construct.core import Construct
from construct.core import ExprAdapter
import enum
from typing import cast

from midi import MidiNote 


AKAI_SECTOR_SIZE = 0x2000

# The least-significant 16bits (little endian) 
# of the first 97 multiples of 3,333
AKAI_PARTITION_MAGIC = b"".join((
    int(3333 * i & 0xFFFF).to_bytes(2, "little", signed=False)
    for i in range(1,98)
))

S1000_VOLUME_TYPE = 1
S3000_VOLUME_TYPE = 3

FILE_TABLE_END_FLAG             = 0xD747

AKAI_SAMPLE_DATA_OFFSET_S1000   = 0x96
AKAI_SAMPLE_WORDLENGTH          = 0x02

AKAI_SAT_ENTRY_CNT              = 11386
AKAI_SAT_RESERVED_FLAG_STD      = 0x4000
AKAI_SAT_RESERVED_FLAG_V2       = 0x8000
AKAI_SAT_FREE_FLAG              = 0x0000
AKAI_SAT_EOF_FLAG               = 0xC000

AKAI_VOLUME_ENTRY_CNT           = 100

AKAI_AUX_OUTPUT_DISABLED        = 0xFF


class InvalidCharacter(Exception):
    pass


class CharFormat(enum.Enum):
    ASCII   = enum.auto()
    AKAI    = enum.auto()


CHAR_MAP_ZERO      = { CharFormat.ASCII: ord("0"),  CharFormat.AKAI: 0x00 }
CHAR_MAP_NINE      = { CharFormat.ASCII: ord("9"),  CharFormat.AKAI: 0x09 }
CHAR_MAP_SPACE     = { CharFormat.ASCII: ord(" "),  CharFormat.AKAI: 0x0A }
CHAR_MAP_A         = { CharFormat.ASCII: ord("A"),  CharFormat.AKAI: 0x0B }
CHAR_MAP_Z         = { CharFormat.ASCII: ord("Z"),  CharFormat.AKAI: 0x24 }
CHAR_MAP_POUND     = { CharFormat.ASCII: ord("#"),  CharFormat.AKAI: 0x25 }
CHAR_MAP_PLUS      = { CharFormat.ASCII: ord("+"),  CharFormat.AKAI: 0x26 }
CHAR_MAP_MINUS     = { CharFormat.ASCII: ord("-"),  CharFormat.AKAI: 0x27 }
CHAR_MAP_PERIOD    = { CharFormat.ASCII: ord("."),  CharFormat.AKAI: 0x28 }


class VolumeType(enum.IntEnum):
    INACTIVE        = 0x00
    VOLUME_S1000    = 0x01
    VOLUME_S3000    = 0x03
    def __str__(self):
        mapping = {
            self.INACTIVE:      "Inactive Volume",
            self.VOLUME_S1000:  "S1000 Volume",
            self.VOLUME_S3000:  "S3000 Volume"
        }
        return mapping.get(self, "Unknown")


class FileType(enum.IntEnum):
    DRUM            = 0x64
    PROGRAM_S1000   = 0x70
    QL              = 0x71
    SAMPLE_S1000    = 0x73
    EFFECT          = 0x78
    PROGRAM_S3000   = 0xf0
    SAMPLE_S3000    = 0xf3
    def __str__(self):
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


class SampleType(enum.IntEnum):
    S1000   = 0x01
    S3000   = 0x03
    def __str__(self):
        mapping = {
            self.S1000: "S1000 Sample",
            self.S3000: "S3000 Sample"
        }
        return mapping.get(self, "Unknown")


class AkaiLoopType(enum.IntEnum):
    LOOP_IN_RELEASE     = 0x00
    LOOP_UNTIL_RELEASE  = 0x01
    LOOP_INACTIVE       = 0x02
    PLAY_TO_SAMPLE_END  = 0x03
    AS_SAMPLE           = 0x04     # Additional state for velocity zones  
    def __str__(self):
        mapping = {
            self.LOOP_IN_RELEASE:       "Loop in release",
            self.LOOP_UNTIL_RELEASE:    "Loop until release",
            self.LOOP_INACTIVE:         "No loop",
            self.PLAY_TO_SAMPLE_END:    "Play until end",
            self.AS_SAMPLE:             "Loop as sample"
        }
        return mapping.get(self, "Unknown")


class AkaiProgramPriority(enum.IntEnum):
    LOW     = 0
    NORMAL  = 1
    HIGH    = 2
    HOLD    = 3
    def __str__(self):
        mapping = {
            self.LOW:       "Low",
            self.NORMAL:    "Normal",
            self.HIGH:      "High",
            self.HOLD:      "Hold"
        }
        return mapping.get(self, "Unknown")


class AkaiMidiOutput(int):
    OMNI    = cast('AkaiMidiOutput', 0xFF)
    @property
    def is_omni(self):
        result = self == self.OMNI
        return result
    def __str__(self):
        result = "Omni" if self.is_omni else int.__str__(self)
        return result


class AkaiAuxOutput(int):
    OFF: 'AkaiAuxOutput' = cast('AkaiAuxOutput', 0xFF)
    @property
    def is_off(self):
        result = self == self.OFF
        return result
    def __str__(self):
        result = "Off" if self.is_off else int.__str__(self)
        return result


class AkaiVoiceReassign(enum.IntEnum):
    OLDEST      = 0
    QUIETEST    = 1
    def __str__(self):
        mapping = {
            self.OLDEST:    "Oldest",
            self.QUIETEST:  "Quietiest"
        }
        return mapping.get(self, "Unknown")


def parse_akai_tune_cents(obj)->float:
    # line equation: y = m(x-x1) + y1
    M = 100/255
    X1 = -128
    Y1 = -50

    x: int = obj
    if x == 0:
        return 0
    result = M*(x - X1) + Y1
    return result


def build_akai_tune_cents(obj)->int:
    # line equation: y = m(x-x1) + y1
    M = 255/100
    X1 = -50
    Y1 = -128

    x: float = obj
    if x == 0:
        return 0
    result = round(M*(x - X1)) + Y1
    return result


def AkaiTuneCents(subcon: Construct)->ExprAdapter:
    result = ExprAdapter( 
        subcon,   
        lambda  x, y: parse_akai_tune_cents(x),
        lambda  x, y: build_akai_tune_cents(x) 
    )
    return result


def AkaiMidiNote(subcon: Construct)->ExprAdapter:
    result = ExprAdapter(
        subcon, 
        lambda x, y: MidiNote.from_akai_byte(x),
        lambda x, y: MidiNote.to_akai_byte(x)  # type: ignore
    )
    return result

