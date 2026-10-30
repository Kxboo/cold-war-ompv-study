"""Generate the self-contained, synthetic OMPV gather/combine SVG.

Only the standard library and the educational reference model are required.
The figure visualizes bilinear coverage before reveal or final composition.
"""
from html import escape
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples'))
from ompv_reference import combine, gather

ROOT = Path(__file__).resolve().parents[1]

PAPER = '#f5f3ec'
INK = '#263027'
MUTED = '#596451'
LINE = '#cbd1c0'
PALETTE = {2: '#adc9de', 7: '#e5bf78'}
OUTLINES = {2: '#8caabe', 7: '#bea065'}
SANS = 'Arial, Helvetica, sans-serif'
MONO = 'Consolas, Menlo, monospace'


def main():
    index_map = [[7, 7], [2, 7]]
    uv = (.375, .625)
    samples = gather(index_map, uv)
    entries = combine(samples)
    corners = ('TL', 'TR', 'BL', 'BR')
    px, py = uv[0] * len(index_map[0]) - .5, uv[1] * len(index_map) - .5
    x, y = px - math.floor(px), py - math.floor(py)
    factors = ((1-x, 1-y), (x, 1-y), (1-x, y), (x, y))
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="700" '
        'viewBox="0 0 1120 700" role="img" aria-labelledby="title desc">',
        '<title id="title">OMPV: four control samples combine into two distinct materials</title>',
        '<desc id="desc">Synthetic 2 by 2 control map at texel-centre position '
        '(0.25, 0.75), equivalent to normalized UV (0.375, 0.625). '
        'Top-left: ID 7, weight (1-x)(1-y) = 0.1875. '
        'Top-right: ID 7, weight x(1-y) = 0.0625. '
        'Bottom-left: ID 2, weight (1-x)y = 0.5625. '
        'Bottom-right: ID 7, weight xy = 0.1875. '
        'Matching IDs combine: material 2 receives 0.5625; '
        'material 7 receives 0.1875 + 0.0625 + 0.1875 = 0.4375. '
        'Both bars use the same zero-to-one scale. Material 7 is segmented by '
        'its three source samples. Numeric layer order is 2 then 7. '
        'Total bilinear coverage is 1. This is coverage before reveal, '
        'not the final compositing weight. Colours only identify materials; '
        'no game textures are included.</desc>',
        f'<rect x="1" y="1" width="1118" height="698" rx="18" '
        f'fill="{PAPER}" stroke="{LINE}" stroke-width="2"/>',
    ]

    def text(tx, ty, value, size=18, colour=INK, weight='normal',
             family=SANS, anchor='start', spacing=None):
        attributes = (f'x="{tx}" y="{ty}" font-family="{family}" font-size="{size}" '
                      f'font-weight="{weight}" fill="{colour}" text-anchor="{anchor}"')
        if spacing is not None:
            attributes += f' letter-spacing="{spacing}"'
        svg.append(f'<text {attributes}>{escape(str(value))}</text>')

    def rect(rx, ry, width, height, fill, stroke=None, radius=0):
        attributes = (f'x="{rx:g}" y="{ry:g}" width="{width:g}" '
                      f'height="{height:g}" fill="{fill}"')
        if stroke:
            attributes += f' stroke="{stroke}"'
        if radius:
            attributes += f' rx="{radius}"'
        svg.append(f'<rect {attributes}/>')

    def line(x1, y1, x2, y2, colour=LINE, width=1):
        svg.append(f'<path d="M{x1:g} {y1:g}L{x2:g} {y2:g}" fill="none" '
                   f'stroke="{colour}" stroke-width="{width}"/>')

    text(32, 36, 'SYNTHETIC OMPV / GATHER + COMBINE', 15, MUTED, spacing=1.5)
    text(32, 82, 'Four samples. Two distinct materials.', 38, family='Georgia, serif')
    text(32, 118, 'Keep the IDs categorical. Add the weights only when the IDs match.', 20, MUTED)
    line(32, 143, 1088, 143)

    # Two stages use the same positions and colours throughout the figure.
    for tx, label, caption, step in (
        (32, 'Gather four control samples', 'Local fractions: x = 0.25, y = 0.75', '01'),
        (464, 'Combine, then sort by ID', 'Bilinear coverage · both bars use a 0–1 scale', '02'),
    ):
        text(tx, 181, step, 16, '#a34b27', family=MONO)
        text(tx + 38, 181, label, 22, weight='bold')
        text(tx, 213, caption, 17, MUTED)

    # Weights are computed by the Python model. Products expose their origin.
    for index, (material, weight, _) in enumerate(samples):
        tx, ty = 32 + (index % 2) * 186, 235 + (index // 2) * 150
        rect(tx, ty, 174, 135, PALETTE[material], OUTLINES[material], radius=6)
        text(tx + 15, ty + 29, corners[index], 16, weight='bold', family=MONO)
        text(tx + 159, ty + 31, f'ID {material}', 25, weight='bold', anchor='end')
        text(tx + 15, ty + 76, 'w', 20, family='Georgia, serif')
        text(tx + 42, ty + 76, f'{weight:.4f}', 25, family=MONO)
        left, right = factors[index]
        text(tx + 15, ty + 111, f'{left:.2f} × {right:.2f}', 18, family=MONO)

    # The arrow connects representations; it does not interpolate IDs.
    svg.append(f'<path d="M410 377H445m-9-9 9 9-9 9" fill="none" '
               f'stroke="{MUTED}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')

    bar_x, bar_width = 484, 584
    for row, entry in enumerate(entries):
        top = 235 + row * 150
        bar_y = top + 84
        members = [(corner, sample[1]) for corner, sample in zip(corners, samples)
                   if sample[0] == entry.material and sample[1] > 0]
        rect(464, top, 624, 135, '#fcfbf6', LINE, radius=6)
        text(484, top + 32, f'Material {entry.material}', 24, weight='bold')
        text(1068, top + 32, f'{entry.coverage:.4f}', 28, weight='bold', family=MONO, anchor='end')
        equation = (' + '.join(f'{weight:.4f}' for _, weight in members)
                    + f' = {entry.coverage:.4f}')
        text(484, top + 64, equation if len(members) > 1 else
             f'{members[0][0]} · the only sample with ID {entry.material}', 18,
             family=MONO if len(members) > 1 else SANS)

        # Identical zero and one endpoints; each segment is width * weight.
        rect(bar_x, bar_y, bar_width, 26, '#e3e6db')
        accumulated = 0.
        for corner, weight in members:
            start = bar_x + bar_width * accumulated
            segment_width = bar_width * weight
            rect(start, bar_y, segment_width, 26, PALETTE[entry.material])
            if accumulated:
                line(start, bar_y, start, bar_y + 26, PAPER, 2)
            text(start + segment_width / 2, bar_y + 19, corner, 16, weight='bold', family=MONO, anchor='middle')
            accumulated += weight
        for tick in (0, .25, .5, .75, 1):
            tick_x = bar_x + bar_width * tick
            line(tick_x, bar_y + 28, tick_x, bar_y + 32, '#7c8970')
            text(tick_x, bar_y + 47, f'{tick:g}', 15, MUTED, family=MONO,
                 anchor='start' if tick == 0 else 'end' if tick == 1 else 'middle')

    text(32, 551, 'Load order: TL, TR, BL, BR', 17, MUTED)
    text(464, 551, 'Numeric layer order:', 18, MUTED)
    text(652, 551, '2 → 7', 22, weight='bold', family=MONO)

    rect(32, 580, 1056, 90, '#e7ebdf', radius=6)
    text(52, 607, 'TOTAL BILINEAR COVERAGE', 15, MUTED, spacing=1)
    total_equation = ' + '.join(f'{entry.coverage:.4f}' for entry in entries)
    total_equation += f' = {sum(entry.coverage for entry in entries):.4f}'
    text(52, 645, total_equation, 25, family=MONO)
    line(510, 599, 510, 650, '#bcc6ae')
    text(536, 614, 'Coverage is not the final blend.', 22, weight='bold')
    text(536, 645, 'Reveal is applied later, after numeric ordering.', 18, MUTED)

    svg.append('</svg>')
    path = ROOT / 'assets' / 'ompv-gather.svg'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(svg) + '\n', encoding='utf-8', newline='\n')
    print('Wrote assets/ompv-gather.svg')


if __name__ == '__main__':
    main()
