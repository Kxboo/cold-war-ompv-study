# From captured shader to isolated equations

The historical research used two complementary experiments: execute the supported composition binary with controlled bindings to isolate operations, then compare a translated implementation with a resource-backed reference bake. This chapter covers the first experiment. The later port comparison is in [validation](04-validation.md); its error numbers measure a different task.

The numerical extracts below are published in [shader-experiments.json](../evidence/shader-experiments.json). That file records the original report and script hashes, the selected report fields and their scope. These are saved measurements, not fresh GPU executions performed while publishing this study. The original game resources, instrumented shader binaries and private research scripts are not bundled.

## How the renderer-owned shader was located

Dumping a painted material's techniques did not identify the terrain composition pass. The later research followed the independently identified compute binary with SHA-256 `6159daeb7882198314ffe9e8b6fab53c1b314258b43a106c1694c5a53d77d9ff` into its renderer-owned references. The inspected `trace_composition_globals.py` implements this read-only discovery procedure:

1. Match the exact binary hash in the saved pool-12 shader inventory, then recover the corresponding asset address from the pool inventory.
2. Search the loaded module's `.data` section for eight-byte-aligned pointers to that asset. An existing globals report or explicit owner RVAs can supply candidates instead of rescanning `.data`.
3. Scan executable sections for candidate RIP-relative instructions referencing those globals or the requested neighborhood. Use the saved PE `.pdata` function bounds to identify surrounding functions.
4. Read each selected function twice, disassemble it, and record whether the candidate reference begins on a decoded instruction boundary. Reread the asset header before accepting the report.

The scanner bounds its reads and logs unreadable chunks. Repeated function/header equality is evidence of stability within those reads; it does not turn the global scan into an atomic snapshot. Candidate byte-pattern matches are also weaker evidence until checked against instruction boundaries and surrounding code.

This historical procedure is distinct from the production extractor. The public extractor consumes the established composition global `module + 0x182aa760`, checks the owner hash/layout, follows the descriptor and saves its bytecode. That public pointer chain is directly reviewable in [CWTerrainBake.h, lines 153–161](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/src/WraithXCOD/WraithXCOD/games/cold_war/terrain/CWTerrainBake.h#L153-L161). It does not itself document how the global was first discovered.

The historical research notes identify pool 12 entry 353, asset hash `0x60e23a45408923cb`, and an 8 × 8 × 1 compute group. They trace the renderer's variant index to `(request.word4 >> 10) & 63`, with the observed dispatch selecting variant 4 at owner `+0xe20` in an array beginning at `+0xe00`. Here that renderer owner is a separate object from the compute-asset owner in the production pointer chain. This association comes from the saved owner-code trace and notes, not from the controlled numerical reports alone. Only the identified variant was executed in these experiments.

## Establishing the distortion binding

The saved shader-argument evidence contains 13 records with a 12-byte stride. Argument index 6 has type `0x407`, location 0, size 1, buffer 0 and value 120. The research associates that argument with code-image index 120 and shader resource `terrainDistort t0`, then traces the CPU-side setter at RVA `0xb8e2592` to the image global at RVA `0x1a188058`. See the `binding` object in [the evidence extract](../evidence/shader-experiments.json).

The retained distortion payload metadata identifies a 256 × 256, one-level BC1_UNORM image (DXGI format 71), 32,768 bytes, with SHA-256 `ce934bb5d4ca1bf22985a8a7bcd16f4bc9a0a56577ee16726a61397ea28e7e92`. The payload was reported as a stable read. The public capture follows this same image global and requires full-resolution acquisition. [Production lookup](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/src/WraithXCOD/WraithXCOD/games/cold_war/terrain/CWTerrainBake.h#L153-L154).

This establishes a resource association, not the complete sampler descriptor. The saved argument evidence records sampler key `0x12` and explicitly says the descriptor was not decoded. Linear wrap is a replay assumption, also disclosed by [the baker's limitations](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L21-L28).

## Isolating selection and duplicate combination

The reference evaluates intermediates exposed by an instrumented copy of the supported DXIL. The baseline reassembly comparison reports maximum absolute error zero for all three outputs. This provides a useful check before interpreting modified intermediates; it does not validate every possible instrumentation change or driver.

For the observed square-map variant, selection uses the tile width `N` for both coordinate axes:

```text
p = mapUV * N + 0.5
q = floor(p)
f = p - q
low  = clamp(q - 1, 0, N - 1)
high = clamp(q,     0, N - 1)
```

This is equivalent to the usual half-texel `mapUV * N - 0.5` convention when the lower/upper coordinates are expressed consistently. The D3D gather component order in the inspected reference is bottom-left, bottom-right, top-right, top-left. The teaching diagram uses top-left, top-right, bottom-left, bottom-right for readability; weights must be permuted with their samples.

The shader selects IDs in ascending order and merges the bilinear weights of repeated IDs. The temporary exhausted-entry value is **256**, outside the valid byte range; **255 remains a material ID**. A zero-weight corner can still supply the lowest ID in the gathered list. The controlled composition path treats that first selected material as its opaque base, then skips later layers with zero coverage. Omitting zero-weight corners before sorting would change that boundary behavior.

Ten saved selection cases, each using a 64 × 64 fixture, report zero ID, weight and coverage error against the instrumented shader. The same research reports that the first 32 bytes of GPU layer records 0–43 match bytes 16–47 of the corresponding CPU slot records. That observed affine-data overlap does not make their full 128-byte and 304-byte layouts identical.

## The observed reveal equation

The generic example in [OMPV mechanics](01-ompv-mechanics.md) teaches the purpose of reveal. The supported shader variant has a more specific equation. For a later material with merged bilinear weight `w`, the controlled path computes `coverage = saturate(2 * w)` and skips it when coverage is zero. The base material is opaque. Reveal is selected by the layer's relevant flag (`0x4` in the inspected path).

Let `mask` be the reveal texture sample, `width = byte82 / 255`, `exponent = byte83 / 255`, and `sat` clamp to `[0, 1]`:

```text
c        = sat(0.998 * coverage + 0.001)
inverse  = sat(1 - c)
low      = sat(inverse - width * pow(c, exponent))
high     = sat(inverse + width * pow(inverse, exponent))
raw      = sat((mask - low) / (high - low))
endpoint = sat((coverage - 0.99) * 100)
alpha    = max(raw, endpoint)
```

For `high == low`, the inspected reference's division/saturation policy gives `raw = 1` when `mask > low`, otherwise `0` (including the `0/0` case). The endpoint maximum is then applied. This edge case matters when width is zero; it must not silently become an arbitrary epsilon-width ramp. Zero coverage is skipped before evaluating reveal in the controlled blend.

The reveal texture descriptor comes from bits 14–27 of the word at layer byte offset 108, with its own scale field at byte 48. It is not automatically the material's displacement texture. The saved 25-case reveal report has zero input error and maximum shape/UV/endpoint error `1.1920928955078125e-7`.

The interactive explorer keeps an **observed equation** mode separate from its illustrative reveal mode. The former reproduces this scalar equation with synthetic masks and colours; it does not recreate the full material shader, texture addressing or weather state.

## Ordered blending and colour space

The controlled final-colour experiment uses flag-`0x5` layers to exercise colour plus reveal while excluding unrelated features. Starting with the opaque base, each later material applies:

```text
colour = colour + (layerColour - colour) * alpha
```

Blending occurs in linear space. After all layers, the result is clamped and encoded to sRGB once. This differs from blending already encoded colours or treating merged coverage as the final visible contribution. For alphas `a1` and `a2`, for example, the final contributions are `(1-a1)*(1-a2)` for the base, `a1*(1-a2)` for the middle layer and `a2` for the top layer.

Sixteen saved cases of 4096 pixels each report a maximum encoded-colour error of `3.5762786865234375e-7` and zero alpha error. These fixtures support the isolated sorting, coverage, reveal and linear-blending sequence for the tested variant. They do not prove the absolute application of Cold War's RGB control map, all material flags, or the final lit terrain appearance.

## Distortion changes selection before material evaluation

The tested distortion operation samples the distortion image at `worldXY * frequency`, at level zero, and warps the control-map coordinate:

```text
warpedUV = (mapUV - amplitude) + sampleRG * (2 * amplitude)
```

The inspected tile parameter at byte offset 292 packs frequency and amplitude as two half-floats. The historical capture notes record frequency `0.0019989013671875` and UV amplitude `0.00146484375` for that fixture. These are observed values for one capture, not constants to hard-code for every map. The controlled validator overwrites the same packed fields to test other parameter pairs.

A neutral sample of `(0.5, 0.5)` cancels the displacement. A nonneutral sample can change the gathered integer IDs as well as their weights, so distortion is not merely a final colour detail.

Five controlled frequency/amplitude cases report zero sample, displacement, ID and weight error. A separate resource-backed experiment reports that enabling the captured distortion changed output 0 at approximately **47.73% of mutually covered pixels**. The actual test is whether **any float4 component** differs by more than `1e-6`; this is not an RGB-only statistic. Its covered fraction is approximately 80.18%, and its inputs use reconstructed dispatch constants. It is not a synchronized in-game dispatch replay.

## Normal decoding and the reduction channel

The saved normal test compares sphere-map inversion with the final normalized detail normal exposed by the instrumented original shader. Across 840,696 pixels, maximum decode error is `3.5762786865234375e-7`; packed output matches the uninstrumented original with error zero. The conventional decoder is public in [output_maps.py, lines 11–33](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/output_maps.py#L11-L33). The later BO3 tangent/geometry projection remains a separate adaptation.

The publication audit also found a stale introductory comment in the private translator: it named `vt2.w` as the group-reduction destination. Following the actual translated expression shows that the per-texel replacement value is scaled by `0.00078125`, offset by `0.5`, and written to **`vt2.y`**. The [port chapter](03-shader-port.md) follows that expression. Neither this channel nor `vt2.w` is established by the later saved AO comparison, which measures only `vt2.x`. No full physical interpretation of these remaining channels is claimed here.

## What these experiments establish

| Experiment | Saved extent | Largest reported error | Boundary |
| --- | --- | --- | --- |
| Instrumentation baseline | Three output planes | 0 | Reassembled baseline under saved fixture |
| Selection and merge | 10 × 4096 pixels | 0 | Synthetic bindings, instrumented intermediates |
| Reveal | 25 cases | `1.1920929e-7` | Tested masks, coverage and parameter bytes |
| Final colour | 16 × 4096 pixels | `3.5762787e-7` | Controlled flag-`0x5` layers |
| Distortion math | 5 controlled cases | 0 | Tested frequencies/amplitudes and replay sampler |
| Normal inversion | 840,696 pixels | `3.5762787e-7` | Detail-normal decode, not BO3 projection |

These tests provide stronger support for individual equations than visual resemblance alone. Their scope remains narrower than a full engine match. The [capture workflow](06-capture-workflow.md) explains where resource bytes come from; the [replay contract](07-replay-contract.md) identifies reconstructed state; and [the port validation](04-validation.md) shows how errors grow when those operations are integrated into another implementation.
