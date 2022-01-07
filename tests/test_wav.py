import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))

import unittest

from smpl_extract.wav.base import WavDataChunkStruct
from smpl_extract.wav.base import WavFormatChunkContainer 
from smpl_extract.wav.base import WavFormatChunkStruct


class WaveTest(unittest.TestCase):


    def test_wave_data_construct_consumes_generator(self):
        
        wave_data = [bytes(b"\x01\x02"), bytes(b"\x03\x04")]
        def data_generator():
            for data in wave_data:
                output = bytes(data)
                yield output

        generator_instance = data_generator()
        
        result = WavDataChunkStruct.build(generator_instance)  # type: ignore
        return self.assertEqual(result, bytes(b"\x01\x02\x03\x04"))
    

    def test_wave_format_header_correct_byte_rate(self):

        header_data = WavFormatChunkContainer(
            audio_format=1,
            channel_cnt=2,
            sample_rate=48000,
            bits_per_sample=16
        )
        
        result_raw = WavFormatChunkStruct.build(header_data)
        result = WavFormatChunkStruct.parse(result_raw)
        return self.assertEqual(result.byte_rate, 2*2*48000)

    
    def test_wave_format_header_correct_block_align(self):

        header_data = WavFormatChunkContainer(
            audio_format=1,
            channel_cnt=2,
            sample_rate=48000,
            bits_per_sample=16
        )
        
        result_raw = WavFormatChunkStruct.build(header_data)
        result = WavFormatChunkStruct.parse(result_raw)
        return self.assertEqual(result.block_align, 2*2)


if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit as err:
        pass
    pass

