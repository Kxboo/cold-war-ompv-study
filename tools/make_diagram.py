"""Generate the original synthetic OMPV diagram; standard library only."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples'))
from ompv_reference import combine, gather

ROOT = Path(__file__).resolve().parents[1]


def main():
    samples = gather([[7, 7], [2, 7]], (.375, .625))
    entries = combine(samples)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="400" viewBox="0 0 1120 400" role="img" aria-labelledby="title desc">',
           '<title id="title">OMPV gathers IDs and combines their coverage</title>',
           '<desc id="desc">Synthetic example: IDs 7,7,2,7 have weights 0.1875,0.0625,0.5625,0.1875. Material 2 combines to 0.5625, material 7 to 0.4375.</desc>',
           '<rect width="1120" height="400" rx="16" fill="#101b29"/>',
           '<g font-family="Arial, sans-serif" fill="#ecf2fa">',
           '<text x="32" y="42" font-size="25" font-weight="bold">Four control samples, two material evaluations</text>',
           '<text x="32" y="70" font-size="15" fill="#b3c5da">Synthetic OMPV example · p = (0.25, 0.75) in texel-centre coordinates</text>']
    palette = {7: '#eab15c', 2: '#83b8f2'}
    for i, (material, weight, _) in enumerate(samples):
        x, y = 32 + (i % 2)*138, 98 + (i // 2)*116
        svg.append(f'<rect x="{x}" y="{y}" width="126" height="104" rx="8" fill="{palette[material]}"/>')
        svg.append(f'<text x="{x+14}" y="{y+35}" font-size="26" fill="#101b29" font-weight="bold">ID {material}</text>')
        svg.append(f'<text x="{x+14}" y="{y+72}" font-size="17" fill="#101b29">w = {weight:.4f}</text>')
    svg.extend(['<path d="M325 208 H420 M408 198 L420 208 L408 218" stroke="#b3c5da" stroke-width="3" fill="none"/>',
                '<text x="335" y="174" font-size="16">combine</text>',
                '<text x="335" y="245" font-size="16">and sort</text>'])
    for row, entry in enumerate(entries):
        y = 115 + row*110
        svg.append(f'<text x="454" y="{y}" font-size="20" font-weight="bold">Material {entry.material}</text>')
        svg.append(f'<rect x="454" y="{y+16}" width="530" height="34" rx="5" fill="#27384d"/>')
        svg.append(f'<rect x="454" y="{y+16}" width="{530*entry.coverage}" height="34" rx="5" fill="{palette[entry.material]}"/>')
        svg.append(f'<text x="1000" y="{y+40}" font-size="18">{entry.coverage:.4f}</text>')
    svg.extend(['<text x="454" y="321" font-size="15" fill="#b3c5da">Coverage sums to 1. Reveal is a later operation.</text>',
                '<text x="32" y="372" font-size="15" fill="#b3c5da">Integer IDs stay categorical. Colour controls follow their associated material.</text>',
                '</g></svg>'])
    path = ROOT / 'assets' / 'ompv-gather.svg'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(svg) + '\n', encoding='utf8')
    print('Wrote assets/ompv-gather.svg')


if __name__ == '__main__':
    main()
