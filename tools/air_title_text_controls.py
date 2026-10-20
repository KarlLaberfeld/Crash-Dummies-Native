"""Append-only original controls for complete text/prompt and deliberate skip."""
import argparse,shutil
from pathlib import Path
from air_title_actions_reference import read,sha,event_sha,replay,memory_sha
from air_reference import write_json
from reference_backend import reference_class,require_matching_backend
CASES=('full-prompt','skip-held')
def tail(case):
    if case=='full-prompt':return [['tick',1200,True],['press','start'],['tick',4,True],['release','start'],['tick',80,True]]
    if case=='skip-held':return [['press','start'],['tick',60,True],['release','start'],['tick',80,True]]
    raise ValueError('Unknown first-instruction text case')
def attachment(parent,child,events,changed,setup):
    case=child['inputCase']
    if case not in CASES or changed!=events+tail(case) or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached append-only text controls')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Text controls lack repeated unobserved prefix/full hashes')
def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    if parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed first-instruction text control/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata)
    for case in CASES:
        hashes=[];prefixes=[]
        for _ in range(2):
            p=Reference(str(args.rom),window='null',sound_volume=0)
            try:
                with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
                replay(p,events);prefixes.append(memory_sha(p));replay(p,tail(case));hashes.append(memory_sha(p))
            finally:p.stop(save=False)
        if prefixes!=[parent['controlMemorySha256']]*2 or len(set(hashes))!=1:raise ValueError('Unrepeatable original text case')
        data=dict(**metadata,romSha256=parent['romSha256'],controlMemorySha256=hashes[0],controlDifferences=[],inputCase=case,parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
        attachment(parent,data,events,events+tail(case),setup);folder=args.out/case;folder.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(args.capture/'setup.state',folder/'setup.state');write_json(folder/'events.json',events+tail(case));write_json(folder/'capture-summary.json',data);print(case,'two original prefix/full hashes match',flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path)
    for key in ('capture','out'):parser.add_argument('--'+key,type=Path,required=True)
    prepare(parser.parse_args())
