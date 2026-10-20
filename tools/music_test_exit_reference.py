"""Complete Start return from an accepted music-test loop to page-zero menu."""
import argparse,contextlib,io
from pathlib import Path
from password_return_reference import prepare,capture as capture_return,compare as compare_return
from air_title_start_reference import read

def capture(args):return capture_return(args,after_music_test=True)
def compare(args,_parent_qualified=False):return compare_return(args,_parent_qualified,after_music_test=True)
def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid music-test return batch')
    ignored={'native_base','test_base','test_out','test_control','exit_out','exit_control'}
    common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Mixed music-test return ancestry')
    parents=[]
    for case in cases:
        values={k:v for k,v in vars(case).items() if k not in ('exit_out','exit_control','test_base')};values['native_base']=case.test_base;parents.append(argparse.Namespace(**values))
    from music_test_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture'):
        p=sub.add_parser(mode);p.add_argument('rom',type=Path)
        for name in ('capture','out')+ (('control','parent-out') if mode=='capture' else ()):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path)
    args=parser.parse_args()
    if args.mode=='compare-batch':compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture)[args.mode](args)
if __name__=='__main__':main()
