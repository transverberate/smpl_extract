from construct.core import RangeError
import unittest

from smpl_extract.akai.data_types import AKAI_PARTITION_MAGIC
from smpl_extract.akai.keygroup import KeygroupConstruct
from smpl_extract.akai.keygroup import KeygroupContainer
from smpl_extract.akai.keygroup import VelocityZoneContainer


class AkaiTest(unittest.TestCase):


    def test_akai_partition_magic_valid(self):
        
        valid_magic = (
            b"\x05\x0D\x0A\x1A\x0F\x27\x14\x34\x19\x41\x1E\x4E\x23\x5B"
            b"\x28\x68\x2D\x75\x32\x82\x37\x8F\x3C\x9C\x41\xA9\x46\xB6"
            b"\x4B\xC3\x50\xD0\x55\xDD\x5A\xEA\x5F\xF7\x64\x04\x69\x11"
            b"\x6E\x1E\x73\x2B\x78\x38\x7D\x45\x82\x52\x87\x5F\x8C\x6C"
            b"\x91\x79\x96\x86\x9B\x93\xA0\xA0\xA5\xAD\xAA\xBA\xAF\xC7"
            b"\xB4\xD4\xB9\xE1\xBE\xEE\xC3\xFB\xC8\x08\xCD\x15\xD2\x22"
            b"\xD7\x2F\xDC\x3C\xE1\x49\xE6\x56\xEB\x63\xF0\x70\xF5\x7D"
            b"\xFA\x8A\xFF\x97\x04\xA5\x09\xB2\x0E\xBF\x13\xCC\x18\xD9"
            b"\x1D\xE6\x22\xF3\x27\x00\x2C\x0D\x31\x1A\x36\x27\x3B\x34"
            b"\x40\x41\x45\x4E\x4A\x5B\x4F\x68\x54\x75\x59\x82\x5E\x8F"
            b"\x63\x9C\x68\xA9\x6D\xB6\x72\xC3\x77\xD0\x7C\xDD\x81\xEA"
            b"\x86\xF7\x8B\x04\x90\x11\x95\x1E\x9A\x2B\x9F\x38\xA4\x45"
            b"\xA9\x52\xAE\x5F\xB3\x6C\xB8\x79\xBD\x86\xC2\x93\xC7\xA0"
            b"\xCC\xAD\xD1\xBA\xD6\xC7\xDB\xD4\xE0\xE1\xE5\xEE"
        )

        self.assertEqual(AKAI_PARTITION_MAGIC, valid_magic)

        return True

    
    def test_keygroup_size(self):
        keygroup = KeygroupContainer(
            velocity_zones=[VelocityZoneContainer("test")],
            velocity_to_sample_start=[0,0,0,0],
            aux_out_offset=[1,2,3,4],
            enable_key_tracking=[True,True,True,True]
        )
        keygroup_raw = KeygroupConstruct.build(keygroup)
        self.assertEqual(len(keygroup_raw), 150)
        return


    def test_keygroup_parse_num_zones(self):
        keygroup = KeygroupContainer(
            velocity_zones=(VelocityZoneContainer("test"), VelocityZoneContainer("sec")),
            velocity_to_sample_start=[0,0,0,0],
            aux_out_offset=[1,2,3,4],
            enable_key_tracking=[True,True,True,True],
        )
        keygroup_raw = KeygroupConstruct.build(keygroup)
        keygroup_reparse = KeygroupConstruct.parse(keygroup_raw)
        if keygroup_reparse is None:
            self.fail()
        self.assertEqual(len(keygroup_reparse.velocity_zones), 2)
        return


    def test_keygroup_build_raises_exception_when_too_many_zones(self):
        keygroup = KeygroupContainer(
            velocity_zones=[
                VelocityZoneContainer("test"), 
                VelocityZoneContainer("sec"),
                VelocityZoneContainer("sec2"),
                VelocityZoneContainer("sec3"),
                VelocityZoneContainer("sec4"),
            ],
            velocity_to_sample_start=[0,0,0,0],
            aux_out_offset=[1,2,3,4],
            enable_key_tracking=[True,True,True,True]
        )
        self.assertRaises(
            RangeError, 
            lambda: KeygroupConstruct.build(keygroup)
        )


if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit as err:
        pass
    pass

