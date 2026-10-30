# Validation and reproduction

## Saved shader comparison

**The reference bake runs Cold War’s own captured terrain composition program unchanged.** Greyhound loads the supported shader binary into a D3D12 compute pipeline and binds captured layer textures, records and controls. Its SHA-256 gate identifies the original program. This makes the bake a faithful reference for that program under the documented saved-input configuration: the material logic comes from Cold War itself. Dispatch constants and provisional sampler choices are reconstructed, weather state is omitted, and the capture is not an atomic GPU-frame snapshot. Those state limits remain relevant when comparing to a live game frame. See the [pinned runner](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L177-L178) and [replay contract](07-replay-contract.md).

[shader-validation.json](../evidence/shader-validation.json) is the saved `val_native` report from the zm_silver experiment. It contains **1,048,576 texels**, all valid in both outputs, and **1.0 validity agreement**. The table preserves its measurements, rounded to six decimals.

| Channel | Mean absolute error × 255 | 99th percentile × 255 | Maximum × 255 |
| --- | ---: | ---: | ---: |
| Colour, encoded RGB | 0.113354 | 1.293148 | 112.652756 |
| Normal, encoded XY | 0.017280 | 0.293564 | 25.848127 |
| Roughness | 0.141972 | 1.245334 | 77.652832 |
| Ambient occlusion | 0.144955 | 0.785144 | 17.455154 |

These values are differences in floating output values scaled by 255, before rounding to an 8-bit image. Percentiles pool selected scalar components over mutually valid pixels. The normal row does not measure a three-dimensional vector or an angle. With every texel valid, this fixture does not exercise hole boundaries.

The mean is low while some maxima are large. The report does not explain those outliers. It also does not identify a complete driver/compiler/environment manifest or prove which installation-format round trip produced every input. The handoff notes quote different numbers for some channels; this study uses the actual saved JSON rather than mixing those runs.

## What 99.96% means

The main page expresses the saved mean colour error as a percentage:

```text
100 × (1 − colour_srgb.mae_8bit / 255)
= 100 × (1 − 0.11335447430610657 / 255)
= 99.955547264978%
≈ 99.96%
```

This is the complement of normalized mean absolute colour error for the **one 1024 × 1024 zm_silver tile** in the saved report. The comparison is the translated shader in a D3D11 WARP harness against Cold War’s own shader in Greyhound’s D3D12 WARP reference bake. It is not a percentage of identical pixels, a perceptual similarity metric, or a measured comparison of final in-game images. It does not summarize normal, roughness, AO, geometry or lighting, and it does not remove the outliers or replay limitations described above.

## Saved colour previews

The [reference image](../assets/reference-bake-colour.png) and [translated-shader image](../assets/translated-shader-colour.png) are the retained `bake_colour.png` and `ours_colour.png`, copied without modification. They show actual saved offline shader outputs. The [main-page comparison](https://kxboo.github.io/cold-war-ompv-study/#comparison) displays them alongside a measured error map.

A fresh comparison of their rounded, clipped **8-bit RGB** pixels gives:

| Criterion, requiring all three channels to pass | Pixels | Share |
| --- | ---: | ---: |
| Identical RGB | 862,299 | 82.235241% |
| Absolute error at most 1/255 | 1,036,808 | 98.877716% |
| Absolute error at most 2/255 | 1,042,879 | 99.456692% |
| Absolute error at most 5/255 | 1,046,917 | 99.841785% |

The PNG RGB mean error is **0.1129112244/255**. The unique largest error is at zero-based pixel **(960, 482)**: reference RGB `(96, 77, 65)`, candidate `(181, 180, 178)`, differences `(85, 103, 113)`. Its cause remains untraced. The error overview shows the **largest channel error within each 16 × 16 block**, deliberately enlarging isolated outliers rather than presenting a percentage of bad area.

The candidate PNG reproduces exactly from the retained `vt0.f32` using the original clamp/round conversion. The published floating-output report matches the retained report JSON. However, the matching **raw reference float files have not been located for a fresh recomputation**. PNG statistics do not replace that historical report or measure its normal, roughness and AO channels. [Preview measurements, hashes and bindings](../evidence/saved-colour-audit.json).

The retained harness bindings select RGBA8 UNORM/sRGB uploads. That does not establish validation of BO3’s final compressed assets. It also does not rule out an earlier encode/decode round trip before upload; that needs input-byte provenance. Keep final BO3 recompression, in-game lighting, surface sounds and geometry validation separate from this one-tile material comparison.

## Three evidence levels

The repository distinguishes new synthetic checks, historical instrumented-shader experiments, and comparison of resource-backed shader outputs. A passing check in one level does not substitute for another.

### Synthetic checks included here

Run these from the repository root with Python 3.10+:

```console
python examples/ompv_reference.py
python -m unittest discover -s tests -v
python tools/make_diagram.py
```

Tests exercise coordinate alignment, duplicate accumulation, all 256 IDs, layer order, colour association, border handling and base/reveal behaviour. They validate the educational model's invariants. They are not evidence of Cold War engine equivalence.

With Node.js installed, the Python suite also compares the browser teaching model against the Python reference across 352 cases. Run the JavaScript checks and rebuild the reader as well:

```console
node --test tests/ompv-model.test.mjs
python tools/build_site.py
```

The JavaScript checks include final compositing weights, ID 255, colour association and the observed reveal equation's zero-width/endpoint cases. The site builder checks internal files and heading links, while reader tests check displayed metrics against the saved report. These browser calculations use JavaScript numbers; agreement with Python is not a float32 GPU execution test. GitHub Actions runs these checks with Python 3.12 and Node.js 22 before publishing.

The HLSL companion has entry point `cs_main` and shader model `cs_5_0`. Its resource contract is documented in the file. With an installed Windows SDK:

```console
fxc /T cs_5_0 /E cs_main /Fo out/ompv_reference.cso shaders/ompv_reference.hlsl
```

Create `out/` first. Compilation checks syntax and shader-model compatibility; it does not execute the shader or prove CPU/GPU parity.

### Historical controlled-shader measurements

[shader-experiments.json](../evidence/shader-experiments.json) selects existing reports for selection, reveal, ordered colour, distortion and normal inversion. [The experiments chapter](08-shader-experiments.md) describes the equations, provenance and limits. These checks used the supported binary with controlled or instrumented fixtures; they are separate from both the new browser/Python teaching examples and the later atlas-backed port report above. The original binaries and resource payloads remain external.

### Compare user-supplied captured outputs

The numerical comparator accepts two folders, each containing `vt0.f32`, `vt1.f32` and `vt2.f32`. Each file must be little-endian float32, tightly packed as height × width × four channels, in the same texel order. These inputs are external; no captured output files are bundled.

```console
python -m pip install -r requirements-analysis.txt
python tools/compare_outputs.py REFERENCE_DIR CANDIDATE_DIR --width 1024 --height 1024 --output out/comparison.json
```

The script checks sizes and finite values, reports validity counts and agreement, computes the same channel metrics as the historical comparator, and records SHA-256 hashes using portable input labels. It rejects zero mutually valid pixels instead of producing misleading empty metrics. It does not infer whether two folders represent the same map, tile or dispatch; the operator must establish that alignment.

To create a new shader comparison, follow [the capture workflow](06-capture-workflow.md) to retain the supported binary and required resource state, verify the shader hash, and build/run [Greyhound's reference bake](07-replay-contract.md#commands-and-what-they-actually-produce). Record which dispatch constants and sampler settings were reconstructed. Run a candidate implementation over the same world coordinates and footprint, then compare the raw outputs. The complete local DXIL translator/BO3 package and game resources are not distributed here, so this repository alone cannot reproduce that original rendering run.

Record at least: binary hash, disassembler and compiler versions/options, driver and adapter, dimensions, world origin/step, all resource hashes and formats, sampler settings, mip inventory, output-channel convention, validity policy, and candidate source revision. Archive the raw outputs privately so later metric changes remain auditable.

## Acceptance criteria for further work

Choose thresholds for each intended use before tuning. Report boundary and interior errors separately, include maxima and outlier locations, and use held-out maps or tiles. Add decoded normal angular error when evaluating normal quality. Keep weather/decal exclusions and footprint differences attached to the result. A lower mean on one tile cannot establish general shader equivalence.
