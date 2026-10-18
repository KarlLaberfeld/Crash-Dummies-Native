"""Bind a native build to its source inputs and executable hash (no ROM data)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    paths = [ROOT / 'build.ps1', ROOT / 'VERSION', Path(__file__).resolve()]
    paths += list((ROOT / 'src').glob('*.h')) + list((ROOT / 'src').glob('*.cpp'))
    paths += list((ROOT / 'tests').glob('*.cpp'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def verify(record):
    if record['inputs'] != inputs():
        raise ValueError('Build inputs changed; rebuild before packaging.')
    if record['sourceRevision'] != git('rev-parse', 'HEAD'):
        raise ValueError('Source revision changed; rebuild before packaging.')
    if record['executableSha256'] != digest(ROOT / 'build/CrashDummiesNative.exe'):
        raise ValueError('Executable does not match the build manifest.')


def main():
    pending = ROOT / 'build/build-pending.json'
    target = ROOT / 'build/build-info.json'
    command = sys.argv[1]
    if command == 'begin':
        record = dict(version=(ROOT / 'VERSION').read_text().strip(),
                      sourceRevision=git('rev-parse', 'HEAD'),
                      sourceDirty=bool(git('status', '--porcelain')),
                      inputs=inputs())
        pending.write_text(json.dumps(record, indent=2) + '\n')
        # A failed build must never leave an apparently current identity.
        target.unlink(missing_ok=True)
    elif command == 'finish':
        record = json.loads(pending.read_text())
        record['executableSha256'] = digest(ROOT / 'build/CrashDummiesNative.exe')
        verify(record)
        target.write_text(json.dumps(record, indent=2) + '\n')
    elif command == 'verify':
        record = json.loads(target.read_text())
        verify(record)
        if record['sourceDirty'] or git('status', '--porcelain'):
            raise ValueError('Packages require a clean committed source build.')
        print('Verified clean source revision and executable hash: ' + record['sourceRevision'])
    else:
        raise ValueError('Expected begin, finish or verify')


if __name__ == '__main__':
    main()
