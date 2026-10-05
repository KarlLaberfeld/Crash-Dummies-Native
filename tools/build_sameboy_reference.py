"""Build the optional local-only comparison adapter, never the native game.

Requires official SameBoy v1.0.3 source at .tools/sameboy-reference, the official
open-source dmg_boot.bin at .tools/sameboy-windows-reference and local Zig.
No source/ROM download or game-state modification is performed by this script.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
REVISION='208ba4afabffab9edde416f2dbb8ae459e34adb8'


def build():
    source=ROOT/'.tools/sameboy-reference';compiler=ROOT/'.tools/zig-x86_64-windows-0.16.0/zig.exe'
    boot=ROOT/'.tools/sameboy-windows-reference/dmg_boot.bin'
    if not compiler.is_file() or not boot.is_file():raise ValueError('Missing local Zig/reference boot ROM; see docs/REFERENCE_BACKENDS.md')
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    dirty=subprocess.check_output(['git','-C',str(source),'diff','--name-only','HEAD','--','Core'],text=True).strip()
    if revision!=REVISION or dirty:raise ValueError('Requires unmodified official SameBoy v1.0.3 core')
    excluded={'debugger.c','sm83_disassembler.c','symbol_hash.c','rewind.c','cheats.c','cheat_search.c'}
    files=[str(p) for p in sorted((source/'Core').glob('*.c')) if p.name not in excluded]
    if not files:raise ValueError('Missing reference core sources')
    output=source/'reference-adapter.dll'
    flags=['-std=gnu11','-O2','-shared','-DGB_INTERNAL','-DGB_DISABLE_DEBUGGER','-DGB_DISABLE_REWIND',
           '-DGB_DISABLE_CHEATS','-DGB_DISABLE_CHEAT_SEARCH','-DGB_DISABLE_TIMEKEEPING','-D_GNU_SOURCE',
           '-D_USE_MATH_DEFINES','-DGB_VERSION="1.0.3"','-DGB_COPYRIGHT_YEAR="2026"','-I'+str(source),'-o',str(output)]
    environment=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(ROOT/'.tools/zig-cache'),ZIG_LOCAL_CACHE_DIR=str(ROOT/'.tools/zig-local-cache'))
    subprocess.run([str(compiler),'cc',*flags,*files,str(ROOT/'tools/sameboy_reference_bridge.c'),'-lwinmm','-lws2_32'],env=environment,check=True)
    metadata=dict(emulator='SameBoy',version='1.0.3',sourceRevision=revision,model='DMG-B',referenceObserver='execution-callback-v1',graphicsStorageObserver='direct-vram-pause-v1',referenceOnly=True,
                  dllSha256=hashlib.sha256(output.read_bytes()).hexdigest(),bootRomSha256=hashlib.sha256(boot.read_bytes()).hexdigest())
    (source/'reference-build.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':build()
