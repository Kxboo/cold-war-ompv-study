"""Synthetic OMPV gather/combine model; no capture or engine dependencies.

Coordinates are normalized UV, converted to texel centres by uv*size - 0.5.
Colour controls and material colours in this example are linear values.
The illustrative reveal/tint rule is not a recovered Cold War implementation.
"""
from dataclasses import asdict, dataclass
import json
import math


@dataclass(frozen=True)
class Contribution:
    material: int
    coverage: float
    weighted_control: tuple[float, float, float]

    @property
    def mean_control(self):
        return tuple(value / self.coverage for value in self.weighted_control)


def gather(index_map, uv, controls=None):
    """Return (ID, weight, RGB control) in TL, TR, BL, BR order.

    IDs 0..255 are all valid; there is no byte-valued invalid sentinel.
    Addressing clamps each neighbour, preserving the bilinear weights.
    """
    height = len(index_map)
    width = len(index_map[0]) if height else 0
    if not width or any(len(row) != width for row in index_map):
        raise ValueError('index_map must be a nonempty rectangular grid')
    if any(type(value) is not int or not 0 <= value <= 255
           for row in index_map for value in row):
        raise ValueError('material IDs must be integers from 0 through 255')
    if len(uv) != 2 or not all(math.isfinite(value) for value in uv):
        raise ValueError('UV must contain two finite values')
    if controls is not None:
        if len(controls) != height or any(len(row) != width for row in controls):
            raise ValueError('control grid must match the index grid')
        if any(len(c) != 3 or not all(math.isfinite(v) for v in c)
               for row in controls for c in row):
            raise ValueError('controls must contain finite RGB triples')
    px, py = uv[0] * width - 0.5, uv[1] * height - 0.5
    x0, y0 = math.floor(px), math.floor(py)
    x, y = px - x0, py - y0
    weights = ((1-x)*(1-y), x*(1-y), (1-x)*y, x*y)
    corners = ((x0, y0), (x0+1, y0), (x0, y0+1), (x0+1, y0+1))
    samples = []
    for (cx, cy), weight in zip(corners, weights):
        cx, cy = min(max(cx, 0), width-1), min(max(cy, 0), height-1)
        control = tuple(controls[cy][cx]) if controls is not None else (1., 1., 1.)
        samples.append((index_map[cy][cx], weight, control))
    return samples


def combine(samples):
    """Combine weights and premultiplied controls, then sort numerically."""
    entries = {}
    for material, weight, control in samples:
        if weight <= 0:
            continue
        entry = entries.setdefault(material, [0., [0., 0., 0.]])
        entry[0] += weight
        for channel in range(3):
            entry[1][channel] += weight * control[channel]
    return [Contribution(material, entry[0], tuple(entry[1]))
            for material, entry in sorted(entries.items())]


def reveal_alpha(coverage, reveal):
    """Illustrative GDC-inspired rule for a non-primary layer."""
    return min(1., max(0., 2. * coverage - 1. + reveal))


def composite(contributions, material_colours, reveal_values):
    """Synthetic tint + reveal illustration, with an opaque primary layer."""
    if not contributions:
        raise ValueError('at least one contribution is required')
    colour = (0., 0., 0.)
    for position, item in enumerate(sorted(contributions, key=lambda c: c.material)):
        layer = tuple(a*b for a, b in zip(material_colours[item.material], item.mean_control))
        alpha = 1. if position == 0 else reveal_alpha(item.coverage, reveal_values[item.material])
        colour = tuple((1-alpha)*old + alpha*new for old, new in zip(colour, layer))
    return colour


def main():
    samples = gather([[7, 7], [2, 7]], (0.375, 0.625))
    entries = combine(samples)
    print(json.dumps({
        'example': 'synthetic; not a Cold War capture',
        'uv': [0.375, 0.625],
        'texel_position': [0.25, 0.75],
        'gather_order': ['TL', 'TR', 'BL', 'BR'],
        'gathered': [{'id': i, 'weight': w} for i, w, _ in samples],
        'combined': [asdict(item) for item in entries],
        'illustrative_colour': composite(entries, {2: (0, 0, 1), 7: (1, 0, 0)}, {2: 0, 7: 0.5}),
    }, indent=2))


if __name__ == '__main__':
    main()
