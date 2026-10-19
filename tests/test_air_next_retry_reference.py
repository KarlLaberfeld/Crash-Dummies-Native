"""Synthetic integrity guards; no ROM, timing recordings or original assets."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_next_retry_reference import extension,attachments


def controls():
    parent=dict(controlDifferences=[],controlMemorySha256='parent',romSha256='rom',emulator='SameBoy',version='v',model='model',sourceRevision='revision',referenceObserver='observer')
    child=dict(parent,controlMemorySha256='child',parentControlMemorySha256='parent',parentPrefixHashes=['parent']*2,unhookedControlHashes=['child']*2)
    events=[['tick',4200,True]]
    return parent,child,events,events+[['press','start'],['tick',1,True],['release','start'],['tick',300,True]]


def chain():
    def point(cycle):return dict(cycles=cycle,tick=65535,countdown=76,scroll=64,inputHeld=33,inputPressed=0,musicEnabled=0,player=0,lives=3,stage=1,difficulty=0,display=4,stat=4,lcdc=231,lyc=135,pendingRequests=0,cameraX=4,cameraY=8,mapScratch=16,ready=0,randomState=256,random=256,held=33,pressed=0)
    def record(start,end,**fields):return dict(points=[point(start),point(end)],interrupts=[],precedingDisplays=1,nextRetry=True,followingResult=True,**fields)
    text=record(10,20,campaign=dict(player=0,stage=1,difficulty=0))
    hand=record(0,10);hand['points'][-1].update(lives0=3,lives1=0)
    records={k:record(a,b) for k,a,b in [('exit',20,30),('prefix',30,40),('stage',40,50),('entry',50,60),('gameplay',60,70)]}
    return text,hand,records


class ExtensionIntegrity(unittest.TestCase):
    def setUp(self):self.parent,self.child,self.events,self.extended=controls()
    def run_check(self):extension(self.parent,self.child,self.events,self.extended)
    def reject(self):
        with self.assertRaises(ValueError):self.run_check()
    def test_valid_control(self):self.run_check()
    def test_parent_mismatch(self):self.child['parentControlMemorySha256']='wrong';self.reject()
    def test_parent_events_changed(self):self.extended[0]=['tick',4199,True];self.reject()
    def test_no_parent_history(self):self.events=[];self.reject()
    def test_injected_extension(self):self.extended.append(['write',0xc083,0]);self.reject()
    def test_held_start_changed(self):self.extended[-3]=['tick',2,True];self.reject()
    def test_release_missing(self):self.extended[-2]=['press','start'];self.reject()
    def test_each_backend_key(self):
        for key in ('romSha256','emulator','version','model','sourceRevision','referenceObserver'):
            previous=self.child[key];self.child[key]='other';self.reject();self.child[key]=previous
    def test_each_control_digest_repeated(self):
        for key in ('parentPrefixHashes','unhookedControlHashes'):
            previous=self.child[key];self.child[key]=previous[:1];self.reject();self.child[key]=previous
    def test_each_control_digest_matches(self):
        for key in ('parentPrefixHashes','unhookedControlHashes'):
            previous=self.child[key];self.child[key]=[previous[0],'wrong'];self.reject();self.child[key]=previous
    def test_changed_control_rejected(self):self.child['controlDifferences']=['changed'];self.reject()


class ChainIntegrity(unittest.TestCase):
    def setUp(self):self.text,self.hand,self.records=chain()
    def check(self):attachments(self.text,self.hand,self.records)
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_valid_attachment(self):self.check()
    def test_each_scope_required(self):
        for part in self.records:
            key='followingResult' if part=='exit' else 'nextRetry'
            self.records[part][key]=False;self.reject();self.records[part][key]=True
    def test_every_original_endpoint_attaches(self):
        for part in self.records:
            p=self.records[part]['points'][0];p['cycles']+=4;self.reject();p['cycles']-=4
    def test_each_service_origin_continues(self):
        for part in ('exit','entry','gameplay'):
            self.records[part]['precedingDisplays']+=1;self.reject();self.records[part]['precedingDisplays']-=1
    def test_life_not_reset(self):self.records['prefix']['points'][0]['lives']=5;self.reject()
    def test_life_not_consumed_twice(self):self.records['stage']['points'][-1]['lives']=2;self.reject()
    def test_stunt_not_changed(self):self.records['stage']['points'][0]['stage']=2;self.reject()
    def test_scene_seed_not_reinitialized_again(self):self.records['gameplay']['points'][0]['random']=0;self.reject()
    def test_input_edge_not_manufactured(self):self.records['gameplay']['points'][0]['pressed']=8;self.reject()
    def test_input_history_retained(self):self.records['exit']['points'][0]['inputHeld']=0;self.reject()
    def test_scroll_retained(self):self.records['exit']['points'][0]['scroll']=0;self.reject()
    def test_eliminated_player_rejected(self):self.hand['points'][-1]['lives0']=0;self.reject()
    def test_other_difficulty_requires_owner(self):self.text['campaign']['difficulty']=1;self.reject()


if __name__=='__main__':unittest.main()
