from dataclasses import dataclass
import enum
import re
from typing import Dict
from typing import Tuple


NOTES_IN_OCTAVE = 12
AKAI_SAMPLE_A0  = 21    # C0 at 24, C3 at 60
MIDI_A0         = 21    # C3 at 60


MIDI_NOTE_STR_REGEX = re.compile(r"([A-Ga-g])(#?)(\d)")


class ScaleDegree(enum.IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    def __str__(self):
        return chr(self.value + ord('A'))
    @classmethod
    def from_string(cls, input: str):
        input = input.upper().strip()
        return cls(ord(input) - ord('A'))


@dataclass(frozen=True, repr=False)
class MidiNote:
    scale_degree:   ScaleDegree = ScaleDegree.A 
    is_sharp:       bool        = False
    octave:         int         = 0


    def to_string(self) -> str:
        scale_degree_string = str(self.scale_degree)
        is_sharp_string = "#" if self.is_sharp else ""
        octave_string = str(self.octave)
        return "".join([
            scale_degree_string,
            is_sharp_string,
            octave_string
        ])


    def __str__(self)->str:
        return self.to_string()


    def __repr__(self)->str:
        result = f"MidiNote({self.to_string()})"
        return result


    @classmethod
    def from_string(cls, input: str):
        input = input.upper().strip()
        matches = MIDI_NOTE_STR_REGEX.match(input)
        if matches is None:
            raise re.error("Could not parse note")
        scale_degree = ScaleDegree.from_string(matches.groups()[0])
        is_sharp = len(matches.groups()[1]) > 0
        octave = int(matches.groups()[2])
        result = cls(scale_degree, is_sharp, octave) 
        return result


    @classmethod
    def from_int_a0(cls, byte_in: int):
        scale_table: Dict[int, Tuple[ScaleDegree, bool]] = {
            0x00:   (ScaleDegree.A, False),
            0x01:   (ScaleDegree.A, True),
            0x02:   (ScaleDegree.B, False),
            0x03:   (ScaleDegree.C, False),
            0x04:   (ScaleDegree.C, True),
            0x05:   (ScaleDegree.D, False),
            0x06:   (ScaleDegree.D, True),
            0x07:   (ScaleDegree.E, False),
            0x08:   (ScaleDegree.F, False),
            0x09:   (ScaleDegree.F, True),
            0x0A:   (ScaleDegree.G, False),
            0x0B:   (ScaleDegree.G, True),
        }
        
        octave = byte_in // NOTES_IN_OCTAVE
        scale_degree_raw = byte_in % NOTES_IN_OCTAVE
        scale_degree, is_sharp = scale_table[scale_degree_raw]

        return cls(scale_degree, is_sharp, octave)

    @classmethod
    def from_akai_byte(cls, byte_in: int):
        byte_normalized = byte_in - AKAI_SAMPLE_A0
        return cls.from_int_a0(byte_normalized)


    @classmethod
    def from_midi_byte(cls, byte_in: int):
        byte_normalized = byte_in - MIDI_A0
        return cls.from_int_a0(byte_normalized)

    
    def to_int_a0(self)->int:

        scale_table: Dict[Tuple[ScaleDegree, bool], int] = {
            (ScaleDegree.A, False):    0x00,
            (ScaleDegree.A, True):     0x01,
            (ScaleDegree.B, False):    0x02,
            (ScaleDegree.B, True):     0x03,   # B# = C
            (ScaleDegree.C, False):    0x03,
            (ScaleDegree.C, True):     0x04,
            (ScaleDegree.D, False):    0x05,
            (ScaleDegree.D, True):     0x06,
            (ScaleDegree.E, False):    0x07,
            (ScaleDegree.E, True):     0x08,   # E# = F
            (ScaleDegree.F, False):    0x08,
            (ScaleDegree.F, True):     0x09,
            (ScaleDegree.G, False):    0x0A,
            (ScaleDegree.G, True):     0x0B
        }
        
        byte_out = scale_table[(self.scale_degree, self.is_sharp)] \
            + (NOTES_IN_OCTAVE * self.octave)

        return byte_out


    def to_akai_byte(self)->int:
        byte_offset = self.to_int_a0()
        byte_out = byte_offset + AKAI_SAMPLE_A0
        return byte_out

    
    def to_midi_byte(self)->int:
        byte_offset = self.to_int_a0()
        byte_out = byte_offset + MIDI_A0
        return byte_out

