"""Synthetic ranking rejection and terminal-title attachment integrity."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_game_over_return_reference import analyze


class ReturnScope(unittest.TestCase):
    def setUp(self):
        self.parent=dict(points=[dict(cycles=100,tick=1,countdown=86,inputHeld=33,inputPressed=0)])
        points=[]
        def point(name,**values):
            points.append(dict(name=name,cycles=100+100*len(points),tick=1,countdown=86,inputHeld=33,inputPressed=0,lives0=0,lives1=0,musicEnabled=1,**values))
        point('begin');point('rankEntry');board=[0]*48
        for row in range(8):
            board[6*row+4]=1;point('row',row=row);point('compareEntry',row=row)
            point('compare',row=row,byte=0,amount=0,target=0);point('compare',row=row,byte=1,amount=0,target=1);point('rowDone',row=row,carry=1)
        for name in ('rankReturned','resultReturned','fadeCall','fadeEntry'):point(name)
        start=points[-1]['cycles']
        for _ in range(8):
            point('palette')
            for _ in range(4):point('wait');point('tail')
        point('fadeReturned');point('titleResetEntry',scoresUnchanged=True)
        irqs=[dict(kind='vblank' if i%2 else 'stat',start=start+10+20*i,end=start+15+20*i,returnAddress=0x261d) for i in range(64)]
        self.data=dict(points=points,interrupts=irqs,scores=board)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_rejected_board_and_fade(self):self.assertEqual(len(analyze(self.data,self.parent)),32)
    def test_detached_hold(self):self.parent['points'][0]['cycles']=1;self.reject()
    def test_surviving_player(self):self.data['points'][-1]['lives1']=1;self.reject()
    def test_table_cannot_change(self):self.data['points'][-1]['scoresUnchanged']=False;self.reject()
    def test_a_row_cannot_qualify(self):next(p for p in self.data['points'] if p['name']=='rowDone')['carry']=0;self.reject()
    def test_money_is_not_an_injected_rank(self):next(p for p in self.data['points'] if p['name']=='compare')['amount']=1;self.reject()
    def test_row_cannot_skip_first_byte(self):next(p for p in self.data['points'] if p['name']=='compare')['byte']=1;self.reject()
    def test_all_eight_rows_required(self):self.data['points']=[p for p in self.data['points'] if not(p['name']=='row' and p['row']==7)];self.reject()
    def test_fade_cannot_be_shortened(self):self.data['interrupts'].pop();self.reject()
    def test_vector_owner_cannot_change(self):self.data['interrupts'][0]['returnAddress']=0x261c;self.reject()


if __name__=='__main__':unittest.main()
