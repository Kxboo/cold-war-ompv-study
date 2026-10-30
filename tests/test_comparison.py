from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
try:
    import numpy as np
    from compare_outputs import compare
except ModuleNotFoundError as error:
    if error.name != 'numpy':
        raise
    np = None


@unittest.skipIf(np is None, 'optional NumPy analysis dependency is not installed')
class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ref, self.cand = [Path(self.temp.name) / name for name in ('ref', 'cand')]
        self.ref.mkdir()
        self.cand.mkdir()
        self.array = np.zeros((1, 2, 4), dtype='<f4')
        self.array[..., 3] = 1
        for folder in (self.ref, self.cand):
            for index in range(3):
                self.array.tofile(folder / f'vt{index}.f32')

    def test_identical_inputs(self):
        report = compare(self.ref, self.cand, 2, 1)
        self.assertEqual(report['colour_srgb']['max_8bit'], 0)
        self.assertEqual(report['valid_both'], 2)
        self.assertEqual(report['valid_agreement'], 1)
        self.assertEqual(len(report['input_sha256']), 6)

    def test_mask_disagreement_does_not_pollute_colour(self):
        changed = self.array.copy()
        changed[0, 0, 0] = .25
        changed[0, 1] = [99, 99, 99, 0]
        changed.tofile(self.cand / 'vt0.f32')
        report = compare(self.ref, self.cand, 2, 1)
        self.assertEqual(report['valid_agreement'], .5)
        self.assertEqual(report['valid_both'], 1)
        self.assertAlmostEqual(report['colour_srgb']['mae_8bit'], 21.25, places=4)
        self.assertEqual(report['colour_srgb']['max_8bit'], 63.75)

    def test_empty_overlap_rejected(self):
        changed = self.array.copy()
        changed[..., 3] = 0
        changed.tofile(self.cand / 'vt0.f32')
        with self.assertRaisesRegex(ValueError, 'no mutually valid'):
            compare(self.ref, self.cand, 2, 1)

    def test_nonfinite_rejected(self):
        changed = self.array.copy()
        changed[0, 0, 0] = float('nan')
        changed.tofile(self.cand / 'vt2.f32')
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            compare(self.ref, self.cand, 2, 1)

    def test_truncated_payload_rejected(self):
        (self.ref / 'vt1.f32').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'expected 32 bytes'):
            compare(self.ref, self.cand, 2, 1)


if __name__ == '__main__':
    unittest.main()
