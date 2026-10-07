import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_ui import result_layout_profile


class ResultProfiles(unittest.TestCase):
    def profile(self,data):return result_layout_profile(bytes(data),0)
    def test_character_classes_and_rows(self):
        self.assertEqual(self.profile([0x81,5,5,0,2,3,0x84,4,0x80]),(1,3,1,1,0,0,0,0))
    def test_rectangle_dimensions_and_destination_carries(self):
        self.assertEqual(self.profile([0x81,5,5,0x83,10,9,7,0,0x40,0x80]),(0,0,1,0,0,10,9,1))
    def test_bank_pointer_does_not_become_runtime_instruction(self):
        a=[0x83,10,9,7,0,0x40,0x80];b=[0x83,10,9,6,0xff,0x7f,0x80]
        self.assertEqual(self.profile(a),self.profile(b))
    def test_second_rectangle_rejects(self):
        with self.assertRaises(ValueError):self.profile([0x83,1,1,1,0,0x40,0x83,1,1,1,0,0x40,0x80])
    def test_empty_rectangle_rejects(self):
        with self.assertRaises(ValueError):self.profile([0x83,0,1,1,0,0x40,0x80])
    def test_dynamic_menu_operations_reject(self):
        for op in (0x85,0x86,0x89,0x8b,0xff):
            with self.assertRaises(ValueError):self.profile([op,0x80])


if __name__=='__main__':unittest.main()
