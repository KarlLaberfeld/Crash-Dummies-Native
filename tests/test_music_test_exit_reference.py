"""Post-test context ownership and complete ancestry checks, synthetic only."""
import argparse,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_password_return_reference import fixture
from password_return_reference import analyze
from music_test_exit_reference import compare_many

class MusicReturnEvidence(unittest.TestCase):
    def setUp(self):
        self.data,self.parent=fixture(1);self.data['afterMusicTest']=True;self.data['inputCase']=self.parent['inputCase']='navigation';end=self.parent['points'][-1];end.update(name='end',pressed=8,tune=7);self.data['points'][0]['pressed']=8
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),83)
    def test_exit_scope(self):self.parent['points'][-1]['name']='wait';self.reject()
    def test_start_edge(self):self.parent['points'][-1]['pressed']=0;self.reject()
    def test_case(self):self.data['inputCase']=self.parent['inputCase']='submit-start';self.reject()
    def test_cursor_retained(self):self.parent['points'][-1]['tune']=0;self.reject()
    def test_song_retained(self):self.parent['points'][-1]['song']=10;self.reject()
    def test_destination(self):self.data['target']=3;self.reject()
    def test_no_missing_close(self):self.data['points'].pop(6);self.reject()
    def test_no_missing_open(self):self.data['points'].pop(-3);self.reject()
    def test_final_song(self):self.data['points'][-1]['song']=13;self.reject()
    def test_full_image(self):self.data['maps'][0]=0;self.reject()

class MusicReturnBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('exit'+str(i)),test_base=Path('test'+str(i)),test_out=Path('test-ref'+str(i)),test_control=Path('test-control'+str(i)),exit_out=Path('exit-ref'+str(i)),exit_control=Path('exit-control'+str(i)),return_screen_base=Path('shared')) for i in range(2)]
    def test_every_parent_and_child(self):
        with patch('music_test_reference.compare_many') as parents,patch('music_test_exit_reference.compare') as children:
            compare_many(self.cases());self.assertEqual([c.native_base for c in parents.call_args.args[0]],[Path('test0'),Path('test1')]);self.assertEqual(children.call_count,2)
    def test_distinct_ancestry(self):
        cases=self.cases();cases[1].return_screen_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)
    def test_empty(self):
        with self.assertRaises(ValueError):compare_many([])

if __name__=='__main__':unittest.main()
