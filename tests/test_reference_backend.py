from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from reference_backend import reference_class,require_matching_backend,require_capture_reference


class ReferenceBackendTests(unittest.TestCase):
    def test_unknown_backend_is_rejected_without_loading_an_emulator(self):
        with self.assertRaises(ValueError):reference_class('unknown')

    def test_recordings_from_different_engines_or_revisions_cannot_mix(self):
        metadata=dict(emulator='PyBoy',version='2.7.0')
        require_matching_backend(metadata,metadata)
        with self.assertRaises(ValueError):require_matching_backend(dict(emulator='SameBoy',version='1.0.3'),metadata)
        with self.assertRaises(ValueError):require_matching_backend(dict(emulator='PyBoy',version='2.6.0'),metadata)

    def test_same_version_with_different_hardware_or_source_is_rejected(self):
        metadata=dict(emulator='SameBoy',version='1.0.3',model='DMG-B',sourceRevision='pinned')
        require_matching_backend(metadata,metadata)
        for key in ('model','sourceRevision'):
            manifest=dict(metadata);manifest[key]='other'
            with self.assertRaises(ValueError):require_matching_backend(manifest,metadata)
        with self.assertRaises(ValueError):require_matching_backend(dict(emulator='SameBoy',version='1.0.3'),metadata)

    def test_legacy_pyboy_measurements_are_distinguished_from_independent_data(self):
        pyboy=dict(emulator='PyBoy',version='2.7.0')
        require_capture_reference(pyboy,{})
        sameboy=dict(emulator='SameBoy',version='1.0.3',model='DMG-B',sourceRevision='pinned')
        with self.assertRaises(ValueError):require_capture_reference(sameboy,{})
        with self.assertRaises(ValueError):require_capture_reference(pyboy,{'reference':sameboy})
        require_capture_reference(sameboy,{'reference':sameboy})


if __name__=='__main__':unittest.main()
