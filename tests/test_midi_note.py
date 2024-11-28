import unittest

from smpl_extract.midi import MidiNote
from smpl_extract.midi import ScaleDegree


class MidiNoteTest(unittest.TestCase):


    def test_parse_midi_note_int_bounds(self):
        lower_raw = 24
        lower_note = MidiNote(ScaleDegree.C, False, 0)
        lower_parsed = MidiNote.from_midi_byte(lower_raw)
        self.assertEqual(lower_note, lower_parsed)
        
        upper_raw = 127
        upper_note = MidiNote(ScaleDegree.G, False, 8)
        upper_parsed = MidiNote.from_midi_byte(upper_raw)
        self.assertEqual(upper_parsed, upper_note)


    def test_midi_note_from_string(self):
        c0_str = "C0"
        c0_note = MidiNote(ScaleDegree.C, False, 0)
        c0_parsed = MidiNote.from_string(c0_str)
        self.assertEqual(c0_note, c0_parsed)
        
        cs0_str = "C#0"
        cs0_note = MidiNote(ScaleDegree.C, True, 0)
        cs0_parsed = MidiNote.from_string(cs0_str)
        self.assertEqual(cs0_note, cs0_parsed)

        a4_str = "A4"
        a4_note = MidiNote(ScaleDegree.A, False, 4)
        a4_parsed = MidiNote.from_string(a4_str)
        self.assertEqual(a4_note, a4_parsed)

        c4_str = "C4"
        c4_note = MidiNote(ScaleDegree.C, False, 4)
        c4_parsed = MidiNote.from_string(c4_str)
        self.assertEqual(c4_note, c4_parsed)


    def test_midi_note_from_string_lowercase(self):
        c4_str = "c4"
        c4_note = MidiNote(ScaleDegree.C, False, 4)
        c4_parsed = MidiNote.from_string(c4_str)
        self.assertEqual(c4_note, c4_parsed)

