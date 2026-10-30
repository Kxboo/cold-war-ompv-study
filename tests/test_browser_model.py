"""Compare browser teaching arithmetic against the independent Python example."""
from pathlib import Path
import json
import random
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples'))
from ompv_reference import combine, composite, gather


@unittest.skipUnless(shutil.which('node'), 'Node.js is required for browser/reference parity')
class BrowserParityTests(unittest.TestCase):
    def test_teaching_model_matches_python_across_352_cases(self):
        rng = random.Random(20261029)
        cases = []
        for material in range(256):
            cases.append({'ids': [[material]], 'uv': [.5, .5], 'controls': [[[.3, .7, 1.]]],
                          'colours': {material: [.8, .4, .2]}, 'reveal': {material: .5}})
        # Repeated IDs, exact centres, clamped edges, mixed controls and random UVs.
        for index in range(96):
            ids = [[7, 7], [2, 255]] if index % 2 else [[255, 7], [2, 7]]
            uv = [rng.uniform(-.5, 1.5), rng.uniform(-.5, 1.5)] if index > 3 else [[.375, .625], [.25, .25], [0, 1], [1, 0]][index]
            controls = [[[rng.random() for _ in range(3)] for _ in range(2)] for _ in range(2)]
            colours = {material: [rng.random() for _ in range(3)] for material in (2, 7, 255)}
            reveal = {material: rng.random() for material in (2, 7, 255)}
            cases.append({'ids': ids, 'uv': uv, 'controls': controls, 'colours': colours, 'reveal': reveal})
        result = subprocess.run([shutil.which('node'), str(ROOT / 'tests' / 'check_browser_model.mjs')],
                                input=json.dumps(cases), capture_output=True, text=True, check=True, timeout=30)
        actual = json.loads(result.stdout)
        self.assertEqual(len(actual), len(cases))
        for index, (case, browser) in enumerate(zip(cases, actual)):
            with self.subTest(case=index):
                samples = gather(case['ids'], case['uv'], case['controls'])
                entries = combine(samples)
                self.assertEqual(browser['samples'], [[material, weight, list(control)] for material, weight, control in samples])
                self.assertEqual(len(browser['contributions']), len(entries))
                for observed, expected in zip(browser['contributions'], entries):
                    self.assertEqual(observed['material'], expected.material)
                    self.assertAlmostEqual(observed['coverage'], expected.coverage, places=13)
                    for key in ('weighted_control', 'mean_control'):
                        for value, reference in zip(observed[key], getattr(expected, key)):
                            self.assertAlmostEqual(value, reference, places=13)
                for value, reference in zip(browser['colour'], composite(entries, case['colours'], case['reveal'])):
                    self.assertAlmostEqual(value, reference, places=13)


if __name__ == '__main__':
    unittest.main()
