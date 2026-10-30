# Validation and reproduction

## Saved shader comparison

[shader-validation.json](../evidence/shader-validation.json) is the saved `val_native` report from the zm_silver experiment. It contains **1,048,576 texels**, all valid in both outputs, and **1.0 validity agreement**. The table preserves its measurements, rounded to six decimals.

| Channel | Mean absolute error × 255 | 99th percentile × 255 | Maximum × 255 |
| --- | ---: | ---: | ---: |
| Colour, encoded RGB | 0.113354 | 1.293148 | 112.652756 |
| Normal, encoded XY | 0.017280 | 0.293564 | 25.848127 |
| Roughness | 0.141972 | 1.245334 | 77.652832 |
| Ambient occlusion | 0.144955 | 0.785144 | 17.455154 |

These values are differences in floating output values scaled by 255, before rounding to an 8-bit image. Percentiles pool selected scalar components over mutually valid pixels. The normal row does not measure a three-dimensional vector or an angle. With every texel valid, this fixture does not exercise hole boundaries.

The mean is low while some maxima are large. The report does not explain those outliers. It also does not identify a complete driver/compiler/environment manifest or prove which installation-format round trip produced every input. The handoff notes quote different numbers for some channels; this study uses the actual saved JSON rather than mixing those runs.

## Two reproducibility levels

### Synthetic checks included here

Run these from the repository root with Python 3.10+:

```console
python examples/ompv_reference.py
python -m unittest discover -s tests -v
python tools/make_diagram.py
```

Tests exercise coordinate alignment, duplicate accumulation, all 256 IDs, layer order, colour association, border handling and base/reveal behaviour. They validate the educational model's invariants. They are not evidence of Cold War engine equivalence.

The HLSL companion has entry point `cs_main` and shader model `cs_5_0`. Its resource contract is documented in the file. With an installed Windows SDK:

```console
fxc /T cs_5_0 /E cs_main /Fo out/ompv_reference.cso shaders/ompv_reference.hlsl
```

Create `out/` first. Compilation checks syntax and shader-model compatibility; it does not execute the shader or prove CPU/GPU parity.

### Compare user-supplied captured outputs

The numerical comparator accepts two folders, each containing `vt0.f32`, `vt1.f32` and `vt2.f32`. Each file must be little-endian float32, tightly packed as height × width × four channels, in the same texel order. These inputs are external; no captured output files are bundled.

```console
python -m pip install -r requirements-analysis.txt
python tools/compare_outputs.py REFERENCE_DIR CANDIDATE_DIR --width 1024 --height 1024 --output out/comparison.json
```

The script checks sizes and finite values, reports validity counts and agreement, computes the same channel metrics as the historical comparator, and records SHA-256 hashes using portable input labels. It rejects zero mutually valid pixels instead of producing misleading empty metrics. It does not infer whether two folders represent the same map, tile or dispatch; the operator must establish that alignment.

To create a new shader comparison, capture the supported binary and complete input state, verify the hash in [the evidence chapter](02-cold-war-evidence.md), and build/run [Greyhound's reference bake](05-sources.md#greyhound-reference). Run a candidate implementation over the same world coordinates and footprint, then compare the raw outputs. The complete local DXIL translator/BO3 package and game resources are not distributed here, so this repository alone cannot reproduce that original rendering run.

Record at least: binary hash, disassembler and compiler versions/options, driver and adapter, dimensions, world origin/step, all resource hashes and formats, sampler settings, mip inventory, output-channel convention, validity policy, and candidate source revision. Archive the raw outputs privately so later metric changes remain auditable.

## Acceptance criteria for further work

Choose thresholds for each intended use before tuning. Report boundary and interior errors separately, include maxima and outlier locations, and use held-out maps or tiles. Add decoded normal angular error when evaluating normal quality. Keep weather/decal exclusions and footprint differences attached to the result. A lower mean on one tile cannot establish general shader equivalence.
