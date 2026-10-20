"""Exact logical framebuffer normalization and mismatch checks without game assets."""
import argparse,copy,sys,unittest
from pathlib import Path
from PIL import Image
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ui_frame_reference import WIDTH,HEIGHT,logical_frame,compare_pixels,frame_owners,compare_many
class ExactFrames(unittest.TestCase):
    def test_all_four_original_grays(self):
        image=Image.new('RGB',(WIDTH,HEIGHT));image.putdata([(v,v,v) for v in (255,170,85,0)]*(WIDTH*HEIGHT//4));self.assertEqual(logical_frame(image),bytes([0,1,2,3])*(WIDTH*HEIGHT//4))
    def test_no_fit_or_tolerance(self):
        image=Image.new('RGB',(WIDTH,HEIGHT),(169,169,169))
        with self.assertRaises(ValueError):logical_frame(image)
    def test_colored_theme_not_silently_normalized(self):
        with self.assertRaises(ValueError):logical_frame(Image.new('RGB',(WIDTH,HEIGHT),(170,169,170)))
    def test_wrong_size(self):
        with self.assertRaises(ValueError):logical_frame(Image.new('RGB',(WIDTH-1,HEIGHT)))
    def test_wrong_mode(self):
        with self.assertRaises(ValueError):logical_frame(Image.new('L',(WIDTH,HEIGHT)))
    def test_exact_all_pixels(self):
        result=compare_pixels(bytes([2])*23040,bytes([2])*23040);self.assertEqual(result,dict(comparedPixels=23040,differences=0,firstDifference=None))
    def test_first_pixel_and_full_difference_count(self):
        source=bytes(23040);native=bytearray(source);native[161]=2;native[300]=3;self.assertEqual(compare_pixels(source,native),dict(comparedPixels=23040,differences=2,firstDifference=dict(x=1,y=1,original=0,native=2)))
    def test_last_pixel_is_included(self):
        native=bytearray(23040);native[-1]=1;self.assertEqual(compare_pixels(bytes(23040),native)['firstDifference'],dict(x=159,y=143,original=0,native=1))
    def test_truncated_source(self):
        with self.assertRaises(ValueError):compare_pixels(bytes(23039),bytes(23040))
    def test_truncated_native(self):
        with self.assertRaises(ValueError):compare_pixels(bytes(23040),bytes(23039))
    def test_invalid_source_shade(self):
        with self.assertRaises(ValueError):compare_pixels(bytes([4])*23040,bytes(23040))
    def test_invalid_native_shade(self):
        with self.assertRaises(ValueError):compare_pixels(bytes(23040),bytes([4])*23040)

class FrameOwners(unittest.TestCase):
    def setUp(self):
        frame=dict(name='instruction',cycles=1000,width=WIDTH,height=HEIGHT,bgp=228,display=5,stat=5,lcdc=209,frameSource='sameboy-direct-pixels-v1')
        self.data=dict(kind='instruction',frames=[frame,dict(frame,name='prompt',cycles=2000)]);self.parent=dict(groups=[dict(points=[dict(cycles=1000)]),dict(points=[dict(name='inputReady',cycles=1900),dict(name='inputReady',cycles=2000)])])
    def check(self):return frame_owners(self.data,self.parent)
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_attached_reveal(self):self.assertEqual(self.check(),['instruction','prompt'])
    def test_wrong_kind(self):self.data['kind']='other';self.reject()
    def test_missing_frame(self):self.data['frames'].clear();self.reject()
    def test_wrong_dimensions(self):self.data['frames'][0]['height']=143;self.reject()
    def test_wrong_palette(self):self.data['frames'][0]['bgp']=0;self.reject()
    def test_wrong_observer(self):self.data['frames'][0]['frameSource']='map-reconstruction';self.reject()
    def test_wrong_cycles(self):self.data['frames'][0]['cycles']+=4;self.reject()
    def test_wrong_display(self):self.data['frames'][0]['display']=4;self.reject()
    def test_wrong_stat(self):self.data['frames'][0]['stat']=4;self.reject()
    def test_wrong_lcdc(self):self.data['frames'][0]['lcdc']=195;self.reject()
    def title(self):
        self.data['kind']='title';self.data['frames']=[];self.parent['groups']=[]
        for page in range(1,5):
            time=2000*page;self.parent['groups'].append(dict(name=str(page-1)+'.idle',points=[dict(name='ready',cycles=time-100),dict(name='ready',cycles=time)]))
            self.data['frames'].append(dict(name='title-'+str(page),cycles=time,width=WIDTH,height=HEIGHT,bgp=228,display=0,stat=1,lcdc=195,frameSource='sameboy-direct-pixels-v1'))
        self.parent['groups'].append(dict(name='4.page',points=[dict(cycles=10000)]));self.data['frames'].append(dict(self.data['frames'][0],name='title-0',cycles=10000+2*70224))
    def test_five_attached_stable_titles(self):self.title();self.assertEqual(len(self.check()),5)
    def test_missing_title_page(self):self.title();self.data['frames'].pop();self.reject()
    def test_reordered_title_pages(self):self.title();self.data['frames'].reverse();self.reject()
    def test_detached_title_wait(self):self.title();self.data['frames'][0]['cycles']-=100;self.reject()
    def test_page_zero_before_complete_stable_waits(self):self.title();self.data['frames'][-1]['cycles']=10001;self.reject()
    def test_page_zero_cannot_borrow_later_carousel(self):self.title();self.data['frames'][-1]['cycles']+=70224;self.reject()

class FrameBatches(unittest.TestCase):
    def test_empty_batch(self):
        with self.assertRaises(ValueError):compare_many([])
    def test_parent_qualifications_are_shared_by_family(self):
        cases=[argparse.Namespace(out=Path('instruction-'+str(n)),qualification=argparse.Namespace(native_base=Path(str(n)))) for n in range(2)]+[argparse.Namespace(out=Path('title-'+str(n)),qualification=argparse.Namespace(native_base=Path(str(n)))) for n in range(2)]
        with patch('ui_frame_reference.read',side_effect=lambda path:dict(kind='instruction' if str(path).startswith('instruction') else 'title')),patch('selected_text_reference.compare_many') as instructions,patch('title_cycle_reference.compare_many') as title,patch('ui_frame_reference.compare') as child:
            compare_many(cases);self.assertEqual(instructions.call_count,1);self.assertEqual(title.call_count,1);self.assertEqual(len(instructions.call_args.args[0]),2);self.assertEqual(len(title.call_args.args[0]),2);self.assertEqual(child.call_count,4)
    def test_unknown_kind_rejects_before_parent_work(self):
        with patch('ui_frame_reference.read',return_value=dict(kind='other')),patch('title_cycle_reference.compare_many') as title:
            with self.assertRaises(ValueError):compare_many([argparse.Namespace(out=Path('x'))])
            title.assert_not_called()
if __name__=='__main__':unittest.main()
