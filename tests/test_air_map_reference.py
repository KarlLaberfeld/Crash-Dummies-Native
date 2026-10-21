import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_map_reference import analyze,compare_rows


def fixture():
    startup=dict(boundary='startup',service=0,cycles=1020,pending=1,row=7,camera=128,lastCamera=256,
        buffer=list(range(32)),tiles=[0]*1024,lcd=dict(readBlocked=0))
    before=copy.deepcopy(startup);before.update(boundary='before',cycles=3000)
    after=copy.deepcopy(before);after.update(boundary='after',cycles=3760);after['tiles'][224:256]=after['buffer']
    end=copy.deepcopy(after);end.update(boundary='end',service=1,cycles=4000)
    data=dict(version=1,points=[startup,before,after,end])
    native=[]
    for p in data['points']:
        n=dict(boundary=p['boundary'],cycle=p['cycles']-1000,service=p['service'],pending=p['pending'],row=p['row'])
        n.update({'buffer'+str(i):v for i,v in enumerate(p['buffer'])});n.update({'tile'+str(i):v for i,v in enumerate(p['tiles'])});native.append(n)
    return data,native


class RowEvidence(unittest.TestCase):
    def setUp(self):self.data,self.native=fixture()
    def test_complete_native_staging_and_transfer(self):self.assertEqual(compare_rows(self.data,self.native,1000),[])
    def test_truncated_native_rejects(self):
        self.native.pop()
        with self.assertRaises(ValueError):compare_rows(self.data,self.native,1000)
    def test_truncated_original_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):analyze(self.data)
    def test_missing_last_service_pair_cannot_pass_as_common_prefix(self):
        self.data['points']=self.data['points'][:1]+self.data['points'][-1:]
        with self.assertRaises(ValueError):analyze(self.data)
    def test_reordered_publication_rejects(self):
        self.data['points'][1]['boundary']='after'
        with self.assertRaises(ValueError):analyze(self.data)
    def test_source_transfer_cannot_mutate_buffer(self):
        self.data['points'][2]['buffer'][0]=33
        with self.assertRaises(ValueError):analyze(self.data)
    def test_source_transfer_cannot_change_destination(self):
        self.data['points'][2]['row']=8
        with self.assertRaises(ValueError):analyze(self.data)
    def test_source_transfer_cannot_mutate_other_tiles(self):
        self.data['points'][2]['tiles'][512]=7
        with self.assertRaises(ValueError):analyze(self.data)
    def test_source_work_delay_rejects(self):
        self.data['points'][2]['cycles']+=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_blocked_storage_read_rejects(self):
        self.data['points'][1]['lcd']['readBlocked']=1
        with self.assertRaises(ValueError):analyze(self.data)
    def test_direct_marker_does_not_weaken_cpu_read_default(self):
        self.data['reference']=dict(titleStorageObserver='direct-vram-title-v1')
        for p in self.data['points']:p['tilesReadOwner']='direct-vram-title-v1'
        self.data['points'][0]['lcd']['readBlocked']=1
        with self.assertRaises(ValueError):analyze(self.data)
        self.assertEqual(len(analyze(self.data,direct_storage=True)),4)
    def test_direct_reader_requires_every_boundary_owner(self):
        self.data['reference']=dict(titleStorageObserver='direct-vram-title-v1')
        for p in self.data['points']:p['tilesReadOwner']='direct-vram-title-v1'
        self.data['points'][1].pop('tilesReadOwner')
        with self.assertRaises(ValueError):analyze(self.data,direct_storage=True)
    def test_incomplete_row_bytes_reject(self):
        self.data['points'][0]['buffer'].pop()
        with self.assertRaises(ValueError):analyze(self.data)
    def test_invalid_row_bytes_reject(self):
        self.data['points'][0]['tiles'][0]=255
        with self.assertRaises(ValueError):analyze(self.data)
    def test_native_partial_row_difference_is_reported(self):
        self.native[1]['buffer16']=17;self.assertIn('buffer16',compare_rows(self.data,self.native,1000)[0]['fields'])
    def test_native_map_destination_difference_is_reported(self):
        self.native[2]['tile255']=0;self.assertIn('tile255',compare_rows(self.data,self.native,1000)[0]['fields'])
    def test_native_time_difference_is_reported(self):
        self.native[2]['cycle']+=4;self.assertIn('cycle',compare_rows(self.data,self.native,1000)[0]['fields'])


if __name__=='__main__':unittest.main()
