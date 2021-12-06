import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))


def bytes2int(bytes_in: bytes)->int:
    return int.from_bytes(bytes_in, "little")

