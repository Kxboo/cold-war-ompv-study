"""Compare aligned, little-endian float32 RGBA vt0..vt2 output files.

Metrics match the historical selected-channel comparison. Input files remain
local; reports contain hashes and portable labels, not absolute input paths.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

CHANNELS = {'colour_srgb': (0, slice(0, 3)), 'normal_xy': (1, slice(0, 2)),
            'roughness': (1, slice(2, 3)), 'ao': (2, slice(0, 1))}


def compare(reference, candidate, width, height):
    if width <= 0 or height <= 0:
        raise ValueError('width and height must be positive')
    expected = width * height * 4 * 4
    hashes, inputs = {}, []
    for label, directory in [('reference', reference), ('candidate', candidate)]:
        arrays = []
        for index in range(3):
            name = f'vt{index}.f32'
            path = Path(directory) / name
            if path.stat().st_size != expected:
                raise ValueError(f'{label}/{name}: expected {expected} bytes')
            data = path.read_bytes()
            array = np.frombuffer(data, dtype='<f4').reshape(height, width, 4)
            if not np.isfinite(array).all():
                raise ValueError(f'{label}/{name}: nonfinite values')
            arrays.append(array)
            hashes[f'{label}/{name}'] = hashlib.sha256(data).hexdigest()
        inputs.append(arrays)
    ref, cand = inputs
    ref_valid, cand_valid = ref[0][..., 3] > .5, cand[0][..., 3] > .5
    valid = ref_valid & cand_valid
    if not valid.any():
        raise ValueError('no mutually valid texels; channel errors are undefined')
    report = {'schema': 'ompv-output-comparison-v1', 'width': width, 'height': height,
              'texels': int(valid.size), 'reference_valid': int(ref_valid.sum()),
              'candidate_valid': int(cand_valid.sum()), 'valid_both': int(valid.sum()),
              'valid_agreement': float((ref_valid == cand_valid).mean()),
              'input_sha256': hashes}
    for label, (index, channels) in CHANNELS.items():
        diff = np.abs(cand[index][..., channels] - ref[index][..., channels])[valid]
        report[label] = {'mae_8bit': float(diff.mean() * 255),
                         'p99_8bit': float(np.percentile(diff, 99) * 255),
                         'max_8bit': float(diff.max() * 255)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = compare(args.reference, args.candidate, args.width, args.height)
    except (OSError, ValueError) as error:
        parser.exit(2, f'comparison failed: {error}\n')
    text = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf8')
    print(text, end='')


if __name__ == '__main__':
    main()
