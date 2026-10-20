"""Synthetic title-layout attachment, complete map and service-mask guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_layout_reference import analyze


class TitleLayoutScope(unittest.TestCase):
    def setUp(self):
        events=[(name,-1,-1) for name in ('begin','bootSkipped','callbackReady','layoutCall')]
        for command in range(11):
            events.append(('command',command,-1))
            if command in (2,4,7,9):
                events.append(('rectangleEntry',command,-1));events.extend(('rowReady',command,r) for r in range({2:3,4:5,7:4,9:10}[command]));events.append(('copyReturned',command,-1))
        events.extend((name,-1,-1) for name in ('layoutReturned','statWrite','lcdWrite','compareWrite','windowXWrite','windowYWrite','lcdEnableCall','lcdEnableEntry','lcdWriteReturned','enableEntry'))
        names=[e[0] for e in events];points=[]
        for i,(name,command,row) in enumerate(events):
            points.append(dict(name=name,command=command,row=row,cycles=100+100*i,tick=2,countdown=54,inputHeld=255,inputPressed=1,lcdc=0x5b if i<=names.index('lcdWrite') else 0x43 if i<names.index('lcdWriteReturned') else 0xc3,bank=7 if name=='rowReady' else 1,display=0,stat=int(i>=2),bootShown=True,pending=3))
        points[-1].update(scoresUnchanged=True,lyc=23,windowX=166,windowY=112)
        addresses=[]
        for layer,x,y,w,h in [(0x9800,3,0,14,3),(0x9800,0,13,20,5),(0x9c00,7,0,8,4),(0x9c00,7,4,6,10)]:addresses.extend(layer+(y+r)*32+x+c for r in range(h) for c in range(w))
        stores=[(0xc099,1)]+[(a,i%256) for i,a in enumerate(addresses)]+list(zip((0xff41,0xff40,0xff45,0xff4b,0xff4a,0xff40),(0x44,0x43,23,166,112,0xc3)))
        writes=[dict(cycle=150+i,address=a,value=v) for i,(a,v) in enumerate(stores)];maps=[0]*2048
        for p in writes[1:-6]:maps[p['address']-0x9800]=p['value']
        self.data=dict(points=points,writes=writes,maps=maps,vectors=[]);self.parent=dict(points=[dict(points[0])])
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(analyze(self.data,self.parent),dict(boundaries=55,writes=241,mapBytes=2048))
    def test_detached_reset(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_boot_must_be_complete(self):self.data['points'][0]['bootShown']=False;self.reject()
    def test_no_masked_tick(self):self.data['points'][9]['tick']+=1;self.reject()
    def test_pending_vectors_cannot_execute(self):self.data['vectors'].append(dict(pc=0x40,cycle=180));self.reject()
    def test_all_cells_included(self):self.data['writes'].pop(50);self.reject()
    def test_no_unobserved_map_change(self):self.data['maps'][1023]=1;self.reject()
    def test_score_table_survives(self):self.data['points'][-1]['scoresUnchanged']=False;self.reject()
    def test_window_geometry(self):self.data['points'][-1]['windowY']=113;self.reject()
    def test_pending_requests_retained(self):self.data['points'][-1]['pending']=0;self.reject()
    def test_row_order(self):next(p for p in self.data['points'] if p['name']=='rowReady')['row']=1;self.reject()
    def test_early_bank_restore(self):next(p for p in self.data['points'] if p['name']=='rowReady')['bank']=1;self.reject()
    def test_no_early_lcd_enable(self):self.data['points'][2]['lcdc']=0xc3;self.reject()
    def test_no_pressed_edge_resample(self):self.data['points'][5]['inputPressed']=0;self.reject()


if __name__=='__main__':unittest.main()
