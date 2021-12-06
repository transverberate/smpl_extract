import enum 


AKAI_SECTOR_SIZE = 0x2000

S1000_VOLUME_TYPE = 1
S3000_VOLUME_TYPE = 3

FILE_TABLE_END_FLAG             = 0xD747

AKAI_SAMPLE_DATA_OFFSET_S1000   = 0x96
AKAI_SAMPLE_WORDLENGTH          = 0x02

AKAI_SAT_ENTRY_CNT              = 11386
AKAI_SAT_RESERVED_FLAG_STD      = 0x4000
AKAI_SAT_RESERVED_FLAG_V2       = 0x8000
AKAI_SAT_FREE_FLAG              = 0x0000
AKAI_SAT_EOF_FLAG               = 0xc000

AKAI_VOLUME_ENTRY_CNT           = 100


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
    def to_string(self):
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


class SampleType(enum.IntEnum):
    S1000   = 0x01
    S3000   = 0x03
    def to_string(self):
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
    def to_string(self):
        mapping = {
            self.LOOP_IN_RELEASE:       "Loop in release",
            self.LOOP_UNTIL_RELEASE:    "Loop until release",
            self.LOOP_INACTIVE:         "No loop",
            self.PLAY_TO_SAMPLE_END:    "Play until end"
        }
        return mapping.get(self, "Unknown")

