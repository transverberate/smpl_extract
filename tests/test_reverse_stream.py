import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

from io import BytesIO
import unittest

from smpl_extract.util.stream import BadAlign
from smpl_extract.util.stream import BadReadSize
from smpl_extract.util.stream import StreamReversed


def generate_consecutive_bytes(size: int, offset: int = 0, width = 1, reverse = False):
    a = offset
    b = offset + size
    if reverse:
        f_reversed = reversed
    else:
        f_reversed = lambda x: x

    X = f_reversed(range(a, b))
    x = [int.to_bytes(i, width, "little") for i in X]
    result = b"".join(x)
    return result


class ReverseStream_Test(unittest.TestCase):


    def test_simple_reverse(self):
        initial_bytes = generate_consecutive_bytes(6)
        expected_bytes = generate_consecutive_bytes(6, reverse=True)

        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=1)
        
        resulting_bytes = b""
        while True:
            result = stream_reverse.read(2)
            if len(result) <= 0:
                break
            resulting_bytes += result
        
        self.assertEqual(resulting_bytes, expected_bytes)


    def test_simple_seek_read(self):
        initial_bytes = generate_consecutive_bytes(6)
        expected_bytes = generate_consecutive_bytes(4, reverse=True)

        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=1)
        stream_reverse.seek(2)
        
        resulting_bytes = b""
        while True:
            result = stream_reverse.read(2)
            if len(result) <= 0:
                break
            resulting_bytes += result
        
        self.assertEqual(resulting_bytes, expected_bytes)

    
    def test_block_read_simple_reverse(self):
        initial_bytes = generate_consecutive_bytes(6)
        expected_bytes = generate_consecutive_bytes(6, reverse=True)

        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=1)
        
        resulting_bytes = b""
        while True:
            result = stream_reverse.read(6)
            if len(result) <= 0:
                break
            resulting_bytes += result
        
        self.assertEqual(resulting_bytes, expected_bytes)


    def test_width_2_reverse(self):
        initial_bytes = generate_consecutive_bytes(3, width=2)
        expected_bytes = generate_consecutive_bytes(3, width=2, reverse=True)

        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=2)
        
        resulting_bytes = b""
        while True:
            result = stream_reverse.read(2)
            if len(result) <= 0:
                break
            resulting_bytes += result
        
        self.assertEqual(resulting_bytes, expected_bytes)


    def test_block_read_width_2_reverse(self):
        initial_bytes = generate_consecutive_bytes(3, width=2)
        expected_bytes = generate_consecutive_bytes(3, width=2, reverse=True)

        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=2)
        
        resulting_bytes = b""
        while True:
            result = stream_reverse.read(6)
            if len(result) <= 0:
                break
            resulting_bytes += result
        
        self.assertEqual(resulting_bytes, expected_bytes)


    def test_width_2_seek_read(self):
        initial_bytes = generate_consecutive_bytes(6, width=2)
        expected_bytes = generate_consecutive_bytes(4, width=2, reverse=True)

        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=2)
        stream_reverse.seek(4)
        
        resulting_bytes = b""
        while True:
            result = stream_reverse.read(2)
            if len(result) <= 0:
                break
            resulting_bytes += result
        
        self.assertEqual(resulting_bytes, expected_bytes)


    def test_width_2_seek_bad_align(self):
        initial_bytes = generate_consecutive_bytes(6, width=2)
        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=2)
        
        self.assertRaises(BadAlign, stream_reverse.seek, 3)


    def test_width_2_read_bad_size(self):
        initial_bytes = generate_consecutive_bytes(6, width=2)
        stream = BytesIO(initial_bytes)
        stream_reverse = StreamReversed(stream, len(initial_bytes), sample_width=2)
        
        self.assertRaises(BadReadSize, stream_reverse.read, 3)

