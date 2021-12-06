import enum
from typing import Dict
from typing import Tuple


NOTES_IN_OCTAVE = 12
AKAI_SAMPLE_A0  = 24    # C0 at 24, C3 at 60
MIDI_A0         = 24    # C3 at 60


class MidiNote:


    class ScaleDegree(enum.Enum):
        A = 0
        B = 1
        C = 2
        D = 3
        E = 4
        F = 5
        G = 6
        def to_string(self):
            return chr(self.value + ord('A'))


    def __init__(
            self,
            scale_degree: ScaleDegree,
            is_sharp: bool,
            octave: int
    ) -> None:
        self.scale_degree = scale_degree
        self.is_sharp = is_sharp
        self.octave = octave
        self.string_repr = self.to_string()


    def to_string(self) -> str:
        scale_degree_string = self.scale_degree.to_string()
        is_sharp_string = "#" if self.is_sharp else ""
        octave_string = str(self.octave)
        return "".join([
            scale_degree_string,
            is_sharp_string,
            octave_string
        ])

    
    def __str__(self) -> str:
        return self.to_string()


    @classmethod
    def from_int_a0(cls, byte_in: int):
        scale_table: Dict[int, Tuple['MidiNote.ScaleDegree', bool]] = {
            0x00:   (cls.ScaleDegree.A, False),
            0x01:   (cls.ScaleDegree.A, True),
            0x02:   (cls.ScaleDegree.B, False),
            0x03:   (cls.ScaleDegree.C, False),
            0x04:   (cls.ScaleDegree.C, True),
            0x05:   (cls.ScaleDegree.D, False),
            0x06:   (cls.ScaleDegree.D, True),
            0x07:   (cls.ScaleDegree.E, False),
            0x08:   (cls.ScaleDegree.F, False),
            0x09:   (cls.ScaleDegree.F, True),
            0x0A:   (cls.ScaleDegree.G, False),
            0x0B:   (cls.ScaleDegree.G, True),
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

        scale_table: Dict[Tuple['MidiNote.ScaleDegree', bool], int] = {
            (self.ScaleDegree.A, False):    0x00,
            (self.ScaleDegree.A, True):     0x01,
            (self.ScaleDegree.B, False):    0x02,
            (self.ScaleDegree.B, True):     0x03,   # B# = C
            (self.ScaleDegree.C, False):    0x03,
            (self.ScaleDegree.C, True):     0x04,
            (self.ScaleDegree.D, False):    0x05,
            (self.ScaleDegree.D, True):     0x06,
            (self.ScaleDegree.E, False):    0x07,
            (self.ScaleDegree.E, True):     0x08,   # E# = F
            (self.ScaleDegree.F, False):    0x08,
            (self.ScaleDegree.F, True):     0x09,
            (self.ScaleDegree.G, False):    0x0A,
            (self.ScaleDegree.G, True):     0x0B
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

