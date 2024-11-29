from io import BytesIO
from typing import Iterable
from typing import Union
import unittest
from unittest.mock import patch

from smpl_extract.data_streams import DataStream
from smpl_extract.data_streams import Endianess
from smpl_extract.data_streams import StreamEncoding
from smpl_extract.transcoder import decode_frame
from smpl_extract.transcoder import make_transcoder
from smpl_extract.transcoder import PipelineTranscoder
from smpl_extract.transcoder import PassthroughTranscoder


class TranscoderTest(unittest.TestCase):


    # Stream encoding comparisions
    def test_compare_encodings_with_wrong_object(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = "dummy"
        self.assertNotEqual(a, b)


    def test_compare_encodings_with_equiv_fields(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        self.assertEqual(a, b)


    def test_compare_encodings_with_equiv_fields_2(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=3,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=3,
            is_signed=True
        )
        self.assertEqual(a, b)


    def test_compare_encodings_with_differing_sample_widths(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=4,
            num_interleaved_channels=1,
            is_signed=True
        )
        self.assertNotEqual(a, b)


    def test_compare_encodings_with_differing_endianess(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.BIG,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        self.assertNotEqual(a, b)


    def test_compare_encodings_with_differing_signs(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=False
        )
        self.assertNotEqual(a, b)


    def test_compare_encodings_simple_vs_interleaved(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=2,
            is_signed=True
        )
        self.assertNotEqual(a, b)


    def test_compare_encodings_with_differing_num_channels_values(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=2,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=3,
            is_signed=True
        )
        self.assertNotEqual(a, b)


    def test_compare_encodings_with_differing_num_channels_fields_but_equiv_meaning(self):
        a = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=1,
            is_signed=True
        )
        b = StreamEncoding(
            endianess=Endianess.LITTLE,
            sample_width=2,
            num_interleaved_channels=0,
            is_signed=True
        )
        self.assertEqual(a, b)

    # Decoding frames
    def test_decode_single_simple_stream(self):
        byte_buffer = b"".join([b"\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding()
        )
        result = decode_frame([stream], [0x4])
        self.assertEqual(len(result), 1)
        self.assertTrue(all(x == 0 for x in list(result[0])))


    def test_decode_multi_simple_streams(self):
        byte_buffer_1 = b"".join([b"\x00"] * 0x4)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding()
        )
        byte_buffer_2 = b"".join([b"\x01"] * 0x4)
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding()
        )
        result = decode_frame([stream_1, stream_2], [0x4, 0x4])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(x == 0 for x in list(result[0])))
        self.assertTrue(all(x == 1 for x in list(result[1])))


    def test_decode_single_interleaved_stream(self):
        channels = zip([b"\x00\x00"] * 0x4, [b"\x01\x00"] * 0x4)
        byte_buffer = b"".join((x + y) for x, y in channels)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(num_interleaved_channels=2, sample_width=2)
        )
        result = decode_frame([stream], [0x10])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(x == 0 for x in list(result[0])))
        self.assertTrue(all(x == 1 for x in list(result[1])))
        


    def test_decode_simple_and_interleaved_streams(self):
        channels = zip([b"\x00\x00"] * 0x4, [b"\x01\x00"] * 0x4)
        byte_buffer_1 = b"".join((x + y) for x, y in channels)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding(num_interleaved_channels=2, sample_width=2)
        )
        byte_buffer_2 = b"".join([b"\x02\x00"] * 0x4)
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding(sample_width=2)
        )
        result = decode_frame([stream_1, stream_2], [0x10, 0x8])
        self.assertEqual(len(result), 3)
        self.assertTrue(all(x == 0 for x in list(result[0])))
        self.assertTrue(all(x == 1 for x in list(result[1])))
        self.assertTrue(all(x == 2 for x in list(result[2])))


    # Bad args for make_transcoder
    def test_no_datastream_raises_error(self):
        from smpl_extract.data_streams import NoDataStream  # type: ignore
        self.assertRaises(NoDataStream, make_transcoder, [], StreamEncoding())


    def test_num_datastreams_neq_encoding_num_channels(self):
        channels = zip([b"\x00\x00"] * 0x4, [b"\x01\x00"] * 0x4)
        byte_buffer_1 = b"".join((x + y) for x, y in channels)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding(num_interleaved_channels=2, sample_width=2)
        )
        byte_buffer_2 = b"".join([b"\x02\x00"] * 0x4)
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding(sample_width=2)
        )
        from smpl_extract.data_streams import IncompatibleNumberOfChannels  # type: ignore
        self.assertRaises(
            IncompatibleNumberOfChannels, 
            make_transcoder, 
            [
                stream_1,
                stream_2
            ], 
            StreamEncoding(num_interleaved_channels=2)
        )


    # Selecting proper transcoders
    def test_simple_transcoder_when_src_encoding_eq_dest(self):
        byte_buffer = b"".join([b"\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2)
        )
        dest_encoding = StreamEncoding(sample_width=2)
        result = make_transcoder([stream], dest_encoding=dest_encoding)
        self.assertIsInstance(result, PassthroughTranscoder)


    def test_simple_transcoder_when_src_encoding_eq_dest_2(self):
        byte_buffer = b"".join([b"\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2, num_interleaved_channels=2)
        )
        dest_encoding = StreamEncoding(sample_width=2, num_interleaved_channels=2)
        result = make_transcoder([stream], dest_encoding=dest_encoding)
        self.assertIsInstance(result, PassthroughTranscoder)


    def test_pipeline_transcoder_with_multiple_src_streams(self):
        byte_buffer_1 = b"".join([b"\x00"] * 0x4)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding(sample_width=2)
        )
        byte_buffer_2 = b"".join([b"\x01"] * 0x4)
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding(sample_width=2)
        )
        dest_encoding = StreamEncoding(sample_width=2, num_interleaved_channels=2)
        result = make_transcoder([stream_1, stream_2], dest_encoding=dest_encoding)
        self.assertIsInstance(result, PipelineTranscoder)

    
    # Stream sizing issues
    def transcode_full(self, transcoder: Iterable[bytes]):
        result = b""
        for x in transcoder:
            result += x
        return result


    def test_simple_stream_sizing_issue_does_not_raise_exception(self):
        byte_buffer = b"".join([b"\x00"] * 0x5)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2)
        )
        transcoder = make_transcoder(
            [stream], 
            StreamEncoding(sample_width=2)
        )
        result = self.transcode_full(transcoder)
        self.assertTrue(len(result) == 4)


    def test_pipeline_stream_sizing_issue_does_not_raise_exception(self):
        byte_buffer_1 = b"".join([b"\x00"] * 0x5)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding(sample_width=2)
        )
        byte_buffer_2 = b"".join([b"\x01\x00"] * 0x2 + [b"\x00"])
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding(sample_width=2)
        )
        transcoder = make_transcoder(
            [stream_1, stream_2], 
            StreamEncoding(
                sample_width=2,
                num_interleaved_channels=2
            )
        )
        result = self.transcode_full(transcoder)
        self.assertTrue(len(result) == 2*4)


    # Pipeline byteswaps
    def pipeline_has_processes(
            self, 
            transcoder: Union[PassthroughTranscoder, PipelineTranscoder],
            *expected_process_names: str,
            is_all: bool = True
    ) -> bool:
        if isinstance(transcoder, PassthroughTranscoder):
            return False

        pipeline_process_names = \
            list(x[0] for x in transcoder.pipeline.processes)

        if is_all:
            for process_name in expected_process_names:
                if process_name not in pipeline_process_names:
                    return False
            return True

        else:  # is any
            for process_name in expected_process_names:
                if process_name in pipeline_process_names:
                    return True
            return False


    def test_no_byteswap_when_input_endian_eq_output(self):
        byte_buffer = b"".join([b"\x00\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.LITTLE):
            transcoder = make_transcoder(
                [stream], 
                StreamEncoding(sample_width=2)
            )
        result = not self.pipeline_has_processes(
            transcoder,
            "swap_input_endianess",
            "swap_input_endianess_multi",
            "swap_output_endianess",
            is_all=False
        )
        self.assertTrue(result)


    def test_input_byteswap_when_input_endian_neq_output_and_sys(self):
        byte_buffer = b"".join([b"\x00\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2, endianess=Endianess.LITTLE)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.BIG):
            transcoder = make_transcoder(
                [stream], 
                StreamEncoding(sample_width=2, endianess=Endianess.BIG)
            )
        result = self.pipeline_has_processes(
            transcoder,
            "swap_input_endianess",
            "swap_input_endianess_multi",
            is_all=False
        )
        self.assertTrue(result)


    def test_output_byteswap_when_input_endian_and_sys_neq_output(self):
        byte_buffer = b"".join([b"\x00\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2, endianess=Endianess.LITTLE)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.LITTLE):
            transcoder = make_transcoder(
                [stream], 
                StreamEncoding(sample_width=2, endianess=Endianess.BIG)
            )
        result = self.pipeline_has_processes(
            transcoder,
            "swap_output_endianess",
            is_all=False
        )
        self.assertTrue(result)


    def test_no_byteswap_when_input_endian_eq_output_ignoring_sys_endian(self):
        byte_buffer = b"".join([b"\x00\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.BIG):
            transcoder = make_transcoder(
                [stream], 
                StreamEncoding(sample_width=2)
            )
        result = not self.pipeline_has_processes(
            transcoder,
            "swap_input_endianess",
            "swap_input_endianess_multi",
            "swap_output_endianess",
            is_all=False
        )
        self.assertTrue(result)


    def test_simple_input_byteswap_when_single_input_endian_neq_sys(self):
        byte_buffer = b"".join([b"\x00\x00"] * 0x4)
        stream = DataStream(
            BytesIO(byte_buffer),
            StreamEncoding(sample_width=2)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.BIG):
            transcoder = make_transcoder(
                [stream], 
                StreamEncoding(sample_width=2, endianess=Endianess.BIG)
            )
        result = self.pipeline_has_processes(
            transcoder,
            "swap_input_endianess"
        )
        self.assertTrue(result)


    def test_simple_input_byteswap_when_all_multi_input_endians_neq_sys(self):
        byte_buffer_1 = b"".join([b"\x00\x00"] * 0x4)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding(sample_width=2)
        )
        byte_buffer_2 = b"".join([b"\x01\x00"] * 0x4)
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding(sample_width=2)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.BIG):
            transcoder = make_transcoder(
                [stream_1, stream_2], 
                StreamEncoding(
                    sample_width=2,
                    endianess=Endianess.BIG,
                    num_interleaved_channels=2
                )
            )
        result = self.pipeline_has_processes(
            transcoder,
            "swap_input_endianess"
        )
        self.assertTrue(result)


    def test_multi_input_byteswap_when_some_multi_input_endians_neq_sys(self):
        byte_buffer_1 = b"".join([b"\x00\x00"] * 0x4)
        stream_1 = DataStream(
            BytesIO(byte_buffer_1),
            StreamEncoding(sample_width=2)
        )
        byte_buffer_2 = b"".join([b"\x01\x00"] * 0x4)
        stream_2 = DataStream(
            BytesIO(byte_buffer_2),
            StreamEncoding(sample_width=2, endianess=Endianess.BIG)
        )
        with patch("smpl_extract.transcoder.system_byte_order", Endianess.BIG):
            transcoder = make_transcoder(
                [stream_1, stream_2], 
                StreamEncoding(
                    sample_width=2,
                    endianess=Endianess.BIG,
                    num_interleaved_channels=2
                )
            )
        result = self.pipeline_has_processes(
            transcoder,
            "swap_input_endianess_multi"
        )
        self.assertTrue(result)


if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit as err:
        pass
    pass

