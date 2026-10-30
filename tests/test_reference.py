from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples'))
from ompv_reference import combine, composite, gather, reveal_alpha


class ReferenceTests(unittest.TestCase):
    def test_bilinear_values_and_order(self):
        samples = gather([[1, 2], [3, 4]], (.375, .625))
        self.assertEqual([s[0] for s in samples], [1, 2, 3, 4])
        self.assertEqual([s[1] for s in samples], [.1875, .0625, .5625, .1875])

    def test_texel_center_has_one_contribution(self):
        entries = combine(gather([[1, 2], [3, 4]], (.25, .25)))
        self.assertEqual([(e.material, e.coverage) for e in entries], [(1, 1.)])

    def test_duplicates_conserve_weight_and_sort(self):
        entries = combine(gather([[7, 7], [2, 7]], (.375, .625)))
        self.assertEqual([(e.material, e.coverage) for e in entries], [(2, .5625), (7, .4375)])
        self.assertEqual(sum(e.coverage for e in entries), 1.)

    def test_controls_stay_with_material(self):
        controls = [[(1, 0, 0), (0, 1, 0)], [(0, 0, 1), (1, 1, 1)]]
        entries = combine(gather([[7, 7], [2, 7]], (.375, .625), controls))
        self.assertEqual(entries[0].mean_control, (0., 0., 1.))
        self.assertEqual(entries[1].weighted_control, (.375, .25, .1875))
        for actual, expected in zip(entries[1].mean_control, (6/7, 4/7, 3/7)):
            self.assertAlmostEqual(actual, expected)

    def test_all_byte_ids_including_255(self):
        for material in range(256):
            entry, = combine(gather([[material]], (.5, .5)))
            self.assertEqual((entry.material, entry.coverage), (material, 1.))

    def test_edges_clamp_without_wrapping(self):
        for uv, expected in [((-10, -10), 1), ((10, 10), 4)]:
            entry, = combine(gather([[1, 2], [3, 4]], uv))
            self.assertEqual((entry.material, entry.coverage), (expected, 1.))

    def test_primary_layer_stays_opaque(self):
        entries = combine(gather([[7]], (.5, .5)))
        self.assertEqual(composite(entries, {7: (.2, .4, .8)}, {7: 0}), (.2, .4, .8))

    def test_reveal_example_and_saturation(self):
        self.assertEqual(reveal_alpha(0, 0), 0)
        self.assertEqual(reveal_alpha(1, 1), 1)
        entries = combine(gather([[7, 7], [2, 7]], (.375, .625)))
        self.assertEqual(composite(entries, {2: (0, 0, 1), 7: (1, 0, 0)}, {2: 0, 7: .5}), (.375, 0., .625))

    def test_coverage_invariants_across_grid(self):
        for y in range(-2, 23):
            for x in range(-2, 23):
                entries = combine(gather([[1, 7], [255, 7]], (x/20, y/20)))
                self.assertAlmostEqual(sum(e.coverage for e in entries), 1.)
                self.assertTrue(all(e.coverage > 0 for e in entries))
                self.assertLessEqual(len(entries), 3)

    def test_invalid_inputs_fail(self):
        for grid in ([], [[1], [1, 2]], [[256]], [[-1]], [[1.5]]):
            with self.assertRaises(ValueError):
                gather(grid, (.5, .5))
        with self.assertRaises(ValueError):
            gather([[1]], (float('nan'), .5))
        with self.assertRaises(ValueError):
            gather([[1]], (.5, .5), [])


if __name__ == '__main__':
    unittest.main()
