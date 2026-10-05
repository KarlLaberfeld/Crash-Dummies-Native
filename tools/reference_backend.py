"""Explicit reference-only backend selection. Not used by the Windows build."""
import importlib.metadata
from pathlib import Path
import sys


def reference_class(backend='pyboy',reference_lib=None):
    if backend=='sameboy':
        from sameboy_reference import SameBoy
        return SameBoy,dict(SameBoy.reference_metadata)
    if backend!='pyboy':raise ValueError('Unknown original reference backend')
    if reference_lib:sys.path.insert(0,str(Path(reference_lib).resolve()))
    if importlib.metadata.version('pyboy')!='2.7.0':raise ValueError('Requires PyBoy 2.7.0')
    from pyboy import PyBoy
    return PyBoy,dict(emulator='PyBoy',version='2.7.0',bootRom='PyBoy bundled boot ROM')


def require_matching_backend(manifest,metadata):
    if manifest.get('emulator')!=metadata['emulator'] or manifest.get('version')!=metadata['version']:
        raise ValueError('Reference backend/revision differs from the original capture; do not mix recordings')
    if metadata['emulator']=='SameBoy' and any(manifest.get(k)!=metadata.get(k) or not metadata.get(k) for k in ('model','sourceRevision','referenceObserver')):
        raise ValueError('Independent reference model/source/observer differs from the original capture')


def require_capture_reference(manifest,recording):
    metadata=recording.get('reference')
    if metadata is not None:require_matching_backend(manifest,metadata)
    elif manifest.get('emulator')!='PyBoy' or manifest.get('version')!='2.7.0':
        raise ValueError('Independent measurement is missing explicit reference provenance')
