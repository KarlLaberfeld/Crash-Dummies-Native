import hashlib
import importlib.util
import json
from pathlib import Path
import io
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('verify_package', Path(__file__).resolve().parents[1] / 'tools/verify_package.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleasePackageTests(unittest.TestCase):
    def package(self, mutation=None):
        files = {name: b'synthetic test content' for name in module.EXPECTED}
        build = dict(sourceRevision='abc', version='test', sourceDirty=False,
                     executableSha256=hashlib.sha256(files['CrashDummiesNative.exe']).hexdigest())
        files['build-info.json'] = json.dumps(build).encode()
        manifest = dict(sourceRevision='abc', version='test', sourceDirty=False,
                        containsOriginalData=False, files=[dict(path=p, sha256=hashlib.sha256(b).hexdigest())
                        for p, b in files.items() if p != 'manifest.json'])
        files['manifest.json'] = json.dumps(manifest).encode()
        if mutation:
            mutation(files)
        path = io.BytesIO()
        with zipfile.ZipFile(path, 'w') as z:
            for name, content in files.items():
                z.writestr('preview/' + name, content)
        path.seek(0)
        return path

    def test_complete_package(self):
        self.assertFalse(module.verify(self.package())['containsOriginalData'])

    def test_asset_leak_rejected(self):
        with self.assertRaises(ValueError):
            module.verify(self.package(lambda f: f.update({'air.dat': b'fake'})))

    def test_tampered_executable_rejected(self):
        with self.assertRaises(ValueError):
            module.verify(self.package(lambda f: f.update({'CrashDummiesNative.exe': b'changed'})))

    def test_missing_dependency_rejected(self):
        with self.assertRaises(ValueError):
            module.verify(self.package(lambda f: f.pop('tools/analyze_audio.py')))

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            module.verify(self.package(lambda f: f.update({'../leak': b'fake'})))

    def test_dirty_build_rejected(self):
        def dirty(f):
            m = json.loads(f['manifest.json']);m['sourceDirty'] = True
            f['manifest.json'] = json.dumps(m).encode()
        with self.assertRaises(ValueError):
            module.verify(self.package(dirty))
