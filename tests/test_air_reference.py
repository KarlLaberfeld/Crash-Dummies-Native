import argparse
import csv
import json
from pathlib import Path
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from air_reference import compare


@contextmanager
def scratch_directory():
    # Match the extractor tests' inherited ACLs on restricted Windows hosts.
    base = (Path(__file__).resolve().parents[1] / 'build' / 'test-temp').resolve()
    base.mkdir(parents=True, exist_ok=True)
    root = (base / str(uuid4())).resolve()
    assert root.parent == base
    root.mkdir()
    try:
        yield root
    finally:
        for name in ('trace.json', 'native.csv', 'native.comparison.json', 'native.differences.json'):
            (root / name).unlink(missing_ok=True)
        root.rmdir()


class AirReferenceComparisonTests(unittest.TestCase):
    def run_comparison(self, native, count=1):
        with scratch_directory() as root:
            # Synthetic state only: no ROM or original recording is committed.
            original = dict(tick=11, handler=0x3bb3, seconds=0x31, map=1,
                            flags=32, x=123, done=1)
            trace = dict(pre=[dict(tick=10)] * count, post=[original] * count)
            (root / 'trace.json').write_text(json.dumps(trace), encoding='utf-8')
            path = root / 'native.csv'
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=native)
                writer.writeheader()
                writer.writerow(native)
            with patch('builtins.print'):
                compare(argparse.Namespace(out=root, native_csv=path))
            return json.loads(path.with_suffix('.comparison.json').read_text())

    def native_row(self):
        return dict(tick=10, handler=5, seconds=31, map=1, flags=32, x=123,
                    done=1, anim=99, pending=0)

    def test_representation_normalization_keeps_clock_difference_explicit(self):
        result = self.run_comparison(self.native_row())
        self.assertEqual(result['matchingPrefix'], 1)
        self.assertEqual(result['firstDifferences'], {})
        self.assertEqual(result['originalCounterChangesDuringUpdate'],
                         [dict(update=0, before=10, after=11)])

    def test_animation_and_position_divergence_are_not_hidden_by_clock_alignment(self):
        row = self.native_row()
        row.update(done=0, x=124, pending=1)
        result = self.run_comparison(row)
        self.assertEqual(result['matchingPrefix'], 0)
        self.assertEqual(set(result['firstDifferences']), {'done', 'x'})
        self.assertEqual(result['firstDeferredRequest'], 0)

    def test_truncated_native_trace_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_comparison(self.native_row(), count=2)


if __name__ == '__main__':
    unittest.main()
