import copy,sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_result_accounting_reference import analyze,compare_accounting


def fixture(perfect=False):
    """Source-shaped, zero-amount ledger fixture; no original recordings."""
    names=['begin','readyWait','readyReturned','detailSetup','dayReady','savingsLabel','savingsNumber','savingsNumberReady','savingsDelay','payLabel','payNumber','payLoop',
        'payTest','payDone','payTotal','payShowEnded','timeLabel','timeNumber','timeLoop','timeTest','timeDone','finalSavings','accountingComplete','timerWait','finalMusicStop','musicStopped','dayAdvance','end']
    extent=747 if perfect else 627
    costs={'payTest':60,'timeTest':40,'finalMusicStop':12384,'musicStopped':88,'dayAdvance':40,'timerWait':extent*70224}
    points=[];cycle=1000
    for name in names:
        done=name in ('finalMusicStop','musicStopped','dayAdvance','end')
        points.append(dict(name=name,cycles=cycle,result=7 if perfect else 3,display=2 if perfect else 10,stage=2 if name=='end' else 1,
            pay=0,savings=4,seconds=0,tick=100+extent if done else 100,countdown=1 if done else 687 if perfect else 567,
            musicEnabled=0 if name in ('musicStopped','dayAdvance','end') else 1))
        cycle+=costs.get(name,4000)
    start=next(p['cycles'] for p in points if p['name']=='timerWait');irqs=[]
    for index in range(extent):
        t=start+70224*index+100;irqs.append(dict(kind='stat',start=t,end=t+(288 if perfect else 248),selector=4 if perfect else 0,returnAddress=0x261d))
        t+=456;countdown=max(1,(687 if perfect else 567)-index);parts=[180,704,280,(272 if countdown>1 else 228)+(2164 if perfect else 0),240,64,68,60,120]
        phases={};time=t
        for name,work in zip(['dma','joypad','display','bookkeeping','effects','audioBank','music','restore'],parts):time+=work;phases[name]=time
        time+=parts[-1]
        irqs.append(dict(kind='vblank',start=t,end=time,returnAddress=0x261d,tick=100+index,countdown=countdown,
            held=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=1,phases=phases))
    data=dict(version=1,points=points,interrupts=irqs,polls=[dict(cycles=2000,mode=0),dict(cycles=3000,mode=1)],
        writes=[dict(cycles=2100,address=0x9ded,value=0),dict(cycles=3100,address=0x9dee,value=3)])
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in ('tick','countdown','pay','savings','seconds','stage','musicEnabled')}) for p in points]
    services=[dict(service=33+i,cycle=r['start']-1000,tick=r['tick'],countdown=max(1,r['countdown']-1),display=(272 if r['countdown']>1 else 228)+(2164 if perfect else 0),
        effects=64,music=60,musicEnabled=1,inputHeld=0) for i,r in enumerate(r for r in irqs if r['kind']=='vblank')]
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-1000,owner=2) for r in irqs]
    polls=[dict(cycle=p['cycles']-1000,mode=p['mode']) for p in data['polls']]
    writes=[dict(cycle=p['cycles']-1000,address=p['address'],value=p['value']) for p in data['writes']]
    summary=[dict(end=points[-1]['cycles']-1000,tick=100+extent,countdown=1,displays=33+extent,stats=33+extent,pay=0,savings=4,seconds=0,stage=2)]
    return data,native,services,vectors,polls,writes,summary


class AccountingEvidence(unittest.TestCase):
    def setUp(self):self.data,self.native,self.services,self.irqs,self.polls,self.writes,self.summary=fixture()
    def compare(self):return compare_accounting(self.data,self.native,self.services,self.irqs,self.polls,self.writes,self.summary,1000)
    def test_complete_source_shaped_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_boundary_rejects(self):
        self.native.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_poll_rejects(self):
        self.polls.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_write_rejects(self):
        self.writes.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_irq_rejects(self):
        self.irqs.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_service_rejects(self):
        self.services.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_reordered_source_stage_rejects(self):
        self.data['points'][1]['name']='dayReady'
        with self.assertRaises(ValueError):analyze(self.data)
    def test_wrong_ledger_total_rejects(self):
        self.data['points'][-1]['savings']=5
        with self.assertRaises(ValueError):analyze(self.data)
    def test_wrong_source_timer_guard_work_rejects(self):
        r=self.data['interrupts'][-1];r['phases']['bookkeeping']+=44
        with self.assertRaises(ValueError):analyze(self.data)
    def test_original_counting_primitive_delay_rejects(self):
        self.data['points'][-1]['cycles']+=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_native_poll_mode_difference_reported(self):
        self.polls[0]['mode']=3;self.assertEqual(self.compare()[0]['category'],'poll')
    def test_native_glyph_difference_reported(self):
        self.writes[1]['value']=4;self.assertEqual(self.compare()[0]['category'],'write')
    def test_native_counter_difference_reported(self):
        self.services[-1]['countdown']=0;self.assertEqual(self.compare()[0]['category'],'service')
    def test_native_vector_delay_reported(self):
        self.irqs[1]['vectorCycle']+=4;self.assertEqual(self.compare()[0]['category'],'interrupt')
    def test_unqualified_owner_rejects(self):
        self.irqs[1]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_summary_total_difference_reported(self):
        self.summary[0]['savings']=5;self.assertEqual(self.compare()[0]['category'],'summary')
    def version_two(self):
        self.data['version']=2
        for p,native in zip(self.data['points'],self.native):
            p.update(skip=0,inputHeld=0,inputPressed=0);native.update(skip=0,inputHeld=0,inputPressed=0)
        for r in self.data['interrupts']:
            if r['kind']=='vblank':r['pressed']=0
        for r in self.services:r['inputPressed']=0
    def test_version_two_fresh_sampling(self):
        self.version_two();self.assertEqual(self.compare(),[])
    def test_invalid_original_fresh_edge_rejects(self):
        self.version_two();self.data['interrupts'][1]['pressed']=2
        with self.assertRaises(ValueError):analyze(self.data)
    def test_invalid_latch_rejects(self):
        self.version_two();self.data['points'][2]['skip']=256
        with self.assertRaises(ValueError):analyze(self.data)
    def test_native_latch_difference_reported(self):
        self.version_two();self.native[2]['skip']=2;self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_native_fresh_edge_difference_reported(self):
        self.version_two();self.services[2]['inputPressed']=2;self.assertEqual(self.compare()[0]['category'],'service')
    def test_latch_cannot_remove_arbitrary_loop_boundaries(self):
        self.version_two();self.data['points'][2]['skip']=2;self.data['points'].pop(3)
        with self.assertRaises(ValueError):analyze(self.data)


class PerfectAccountingEvidence(unittest.TestCase):
    def setUp(self):
        self.values=list(fixture(True));self.data=self.values[0];self.data['version']=3
        self.celebrations=[]
        for p,q in zip(self.data['points'],self.values[1]):
            p.update(skip=0,inputHeld=0,inputPressed=0);q.update(skip=0,inputHeld=0,inputPressed=0)
        state=dict(random=257,emitters=[[30+i,143,251,0,1] for i in range(4)])
        for i,(r,q) in enumerate(zip((r for r in self.data['interrupts'] if r['kind']=='vblank'),self.values[2])):
            r.update(pressed=0,visible=[0]*160);q['inputPressed']=0
            r['celebration']=dict(start=r['phases']['display']+20,end=r['phases']['display']+2104,tick=r['tick'],
                before=copy.deepcopy(state),after=copy.deepcopy(state),prepared=[0]*160)
            row=dict(service=33+i,tick=r['tick'],work=2084,random=257,spriteCount=0)
            for j,e in enumerate(state['emitters']):row.update({f'emitter{j}{k}':v for k,v in zip(('x','y','velocity','radius','delay'),e)})
            row.update({f'{name}{j}':0 for name in ('prepared','visible') for j in range(160)})
            self.celebrations.append(row)
    def compare(self):return compare_accounting(*self.values,1000,self.celebrations)
    def test_complete_schema_three_storage_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_native_component_rejects(self):
        with self.assertRaises(ValueError):compare_accounting(*self.values,1000)
    def test_wrong_source_selector_rejects(self):
        self.data['interrupts'][0]['selector']=0
        with self.assertRaises(ValueError):self.compare()
    def test_source_publication_gap_rejects(self):
        self.data['interrupts'][3]['visible'][0]=1
        with self.assertRaises(ValueError):self.compare()
    def test_native_publication_difference_reported(self):
        self.celebrations[3]['visible159']=1;self.assertEqual(self.compare()[0]['category'],'publication')
    def test_missing_native_publication_tail_rejects(self):
        del self.celebrations[0]['visible159']
        with self.assertRaises(ValueError):self.compare()
    def test_component_offset_is_checked(self):
        self.celebrations[0]['service']=0;self.assertIn('celebration',self.compare()[0])

if __name__=='__main__':unittest.main()
