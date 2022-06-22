import enum


# --- UNITS ---
ROLAND_BLOCK_SIZE   = 0x200
ROLAND_CLUSTER_SIZE = 0x2400  # 18 * block size
ROLAND_SAMPLE_WIDTH = 2

MAX_NUM_VOLUME      = 0x80
MAX_NUM_PERFORMANCE = 0x200
MAX_NUM_PATCH       = 0x400
MAX_NUM_PARTIAL     = 0x1000
MAX_NUM_SAMPLE      = 0x2000
NUM_KEYS            = 88

ID_AREA_SIZE        = 0x200
RESERVED_AREA_SIZE  = 0x600
PROGRAM_TEXT_AREA   = 0x80000


# --- LAYOUT: FAT AREA ---
FAT_AREA_OFFSET     = 0x80800
FAT_AREA_SIZE       = 0x20000
FAT_ENTRY_SIZE      = 0x2
FAT_NUM_ENTRIES     = 0x10000

FAT_AREA_ID         = 0xfffa
FAT_FREE_FLAG       = 0x0000
FAT_RESERVED_FLAG   = 0x0001
FAT_ERROR_FLAG      = 0xfff7
FAT_VERSION_1_FLAG  = 0xffff
FAT_VERSION_2_FLAG  = 0xfffe
FAT_END             = 0xfff8
FAT_IS_END_F        = (lambda x: x >= FAT_END)


# --- LAYOUT: DIRECTORY AREA ---
TOTAL_DIRECTORY_AREA_OFFSET         = 0xa0800
TOTAL_DIRECTORY_AREA_SIZE           = 0x6d000

VOLUME_DIRECTORY_AREA_OFFSET        = 0xa0800
VOLUME_DIRECTORY_AREA_SIZE          = 0x1000
VOLUME_DIRECTORY_ENTRY_SIZE         = 0x20

PERFORMANCE_DIRECTORY_AREA_OFFSET   = 0xa1800
PERFORMANCE_DIRECTORY_AREA_SIZE     = 0x4000
PERFORMANCE_DIRECTORY_ENTRY_SIZE    = 0x20

PATCH_DIRECTORY_AREA_OFFSET         = 0xa5800
PATCH_DIRECTORY_AREA_SIZE           = 0x8000
PATCH_DIRECTORY_ENTRY_SIZE          = 0x20

PARTIAL_DIRECTORY_AREA_OFFSET       = 0xad800
PARTIAL_DIRECTORY_AREA_SIZE         = 0x20000
PARTIAL_DIRECTORY_ENTRY_SIZE        = 0x20

SAMPLE_DIRECTORY_AREA_OFFSET        = 0xcd800
SAMPLE_DIRECTORY_AREA_SIZE          = 0x40000
SAMPLE_DIRECTORY_ENTRY_SIZE         = 0x20


# --- LAYOUT: PARAMETER AREA ---
TOTAL_PARAMETER_AREA_OFFSET         = 0x10d800
TOTAL_PARAMETER_AREA_SIZE           = 0x1a8000

VOLUME_PARAMETER_AREA_OFFSET        = 0x10d800
VOLUME_PARAMETER_AREA_SIZE          = 0x8000
VOLUME_PARAMETER_ENTRY_SIZE         = 0x100

PERFORMANCE_PARAMETER_AREA_OFFSET   = 0x115800
PERFORMANCE_PARAMETER_AREA_SIZE     = 0x40000
PERFORMANCE_PARAMETER_ENTRY_SIZE    = 0x200

PATCH_PARAMETER_AREA_OFFSET         = 0x155800
PATCH_PARAMETER_AREA_SIZE           = 0x80000
PATCH_PARAMETER_ENTRY_SIZE          = 0x200

PARTIAL_PARAMETER_AREA_OFFSET       = 0x1d5800
PARTIAL_PARAMETER_AREA_SIZE         = 0x80000
PARTIAL_PARAMETER_ENTRY_SIZE        = 0x80

SAMPLE_PARAMETER_AREA_OFFSET        = 0x255800
SAMPLE_PARAMETER_AREA_SIZE          = 0x60000
SAMPLE_PARAMETER_ENTRY_SIZE         = 0x30


# --- LAYOUT: DATA AREA ---
DATA_AREA_OFFSET    = 0x2b5800

# *Note* 
#        The data area starts at BLOCK 0x15AC
#        and that FAT[2] is the first valid FAT entry.
#        Consequently FAT[2] should point to BLOCK 0x15AC.
#        Since each FAT entry is 18 blocks (1 cluster),
#        FAT[0x0000] should theoretically point to 
#        BLOCK 0x15AC - (2*18) = 0x1588. In bytes, 
#        0x1588 * 0x200 = 0x2b1000
DATA_FAT_OFFSET     = 0x2b1000


# --- ENUMS ---
class FileType(enum.IntEnum):
    NONE        = 0x00
    VOLUME      = 0x40
    PERFORMANCE = 0x41 
    PATCH       = 0x42
    PARTIAL     = 0x43
    SAMPLE      = 0x44
    
    def __str__(self) -> str:
        result = self.name.title()
        return result


class SampleMode(enum.IntEnum):
    MONO    = 0
    STEREO  = 1

    def __str__(self) -> str:
        result = self.name.title()
        return result


class LoopMode(enum.IntEnum):
    FORWARD_END     = 0
    FORWARD_RELEASE = 1
    ONESHOT         = 2
    FORWARD_ONESHOT = 3
    ALTERNATE       = 4
    REVERSE_ONESHOT = 5
    REVERSE_LOOP    = 6

    def __str__(self) -> str:
        result = self.name.replace("_", " ")
        result = result.title()
        return result

