"""Verify the exact ROM-free release ZIP allowlist and all recorded hashes."""
import hashlib
import json
import sys
import zipfile
from pathlib import PurePosixPath

EXPECTED = {'CrashDummiesNative.exe', 'build-info.json', 'RELEASE_NOTES.md',
            'PROVENANCE.md', 'LICENSE', 'README.txt', 'Prepare-Assets.ps1', 'manifest.json'}
EXPECTED |= {'tools/' + name + '.py' for name in (
    'extract', 'extract_air', 'extract_ski', 'extract_bomb', 'extract_cruise',
    'extract_ui', 'extract_audio', 'analyze_audio')}


def verify(path):
    with zipfile.ZipFile(path) as z:
        files = {}
        roots = set()
        for info in z.infolist():
            p = PurePosixPath(info.filename.replace('\\', '/'))
            if p.is_absolute() or '..' in p.parts or len(p.parts) < 2:
                raise ValueError('Unsafe or unexpected archive path')
            roots.add(p.parts[0])
            if info.is_dir():
                continue
            relative = '/'.join(p.parts[1:])
            if relative in files:
                raise ValueError('Duplicate archive member')
            files[relative] = z.read(info)
    if len(roots) != 1 or set(files) != EXPECTED:
        raise ValueError('Package does not match the ROM-free allowlist')
    manifest = json.loads(files['manifest.json'].decode('utf-8-sig'))
    build = json.loads(files['build-info.json'].decode('utf-8-sig'))
    if manifest['containsOriginalData'] or manifest['sourceDirty'] or build['sourceDirty']:
        raise ValueError('Original data or dirty source is not releasable')
    entries = manifest['files']
    if len(entries) != len(files) - 1 or {x['path'] for x in entries} != set(files) - {'manifest.json'}:
        raise ValueError('Manifest does not enumerate every file exactly once')
    for entry in entries:
        if hashlib.sha256(files[entry['path']]).hexdigest() != entry['sha256']:
            raise ValueError('Hash mismatch: ' + entry['path'])
    exe_hash = hashlib.sha256(files['CrashDummiesNative.exe']).hexdigest()
    if exe_hash != build['executableSha256']:
        raise ValueError('Executable build identity mismatch')
    if manifest['sourceRevision'] != build['sourceRevision'] or manifest['version'] != build['version']:
        raise ValueError('Package/build identity mismatch')
    return dict(version=manifest['version'], sourceRevision=build['sourceRevision'],
                executableSha256=exe_hash, files=len(files), containsOriginalData=False)


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1]), indent=2))
