"""Build the reference-free Air timing diagnostic serially at O2."""
import argparse
import os
from pathlib import Path
import subprocess


def build(args):
    root = Path(__file__).resolve().parents[1]
    compiler = args.compiler or root/'.tools/zig-x86_64-windows-0.16.0/zig.exe'
    if not compiler.is_file():raise ValueError('Zig compiler not found; supply --compiler')
    out = args.out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    objects = out.parent/'air-clock-objects';objects.mkdir(exist_ok=True)
    env = dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(root/'.tools/zig-cache'),ZIG_LOCAL_CACHE_DIR=str(root/'.tools/zig-local-cache'))
    sources = ['tools/air_clock_probe.cpp','src/air.cpp','src/game.cpp','src/audio.cpp','src/ui.cpp']
    targets = []
    for source in sources:
        target = objects/(Path(source).stem+'.o');targets.append(str(target))
        print('Compile',source,'at O2',flush=True)
        subprocess.run([str(compiler),'c++','-std=c++17','-O2','-fno-sanitize=all','-Wall','-Wextra','-Wpedantic','-Isrc',
                        '-c',source,'-o',str(target)],cwd=root,env=env,check=True)
    subprocess.run([str(compiler),'c++','-O2',*targets,'-o',str(out)],cwd=root,env=env,check=True)
    print('Built optimized native diagnostic:',out,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path);parser.add_argument('--out',type=Path,default=Path('local/air-clock-probe.exe'))
    build(parser.parse_args())
