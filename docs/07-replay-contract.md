# The offline replay contract

The reference bake separates capture from execution. Once its input files exist, `bake.py` and `run_composition.exe` do not need to read the game. The runner creates its own D3D12 WARP device, reconstructs bindings and executes the captured shader payload. This chapter identifies exactly what is captured, synthesized and measured.

## File roles and stages

| Artifact | Producer | Consumer | Meaning |
| --- | --- | --- | --- |
| `inputs.json` | `CWTerrainBake::Capture` | `bake.py` | Surface mappings, native images, tile/layer files, shader and distortion |
| `generic.bin` | `bake.py` | Runner | Reconstructed per-tile constants |
| `scene.bin` | `bake.py` | Runner | Reconstructed scene constants |
| `dispatch.json` | `bake.py` | Runner | One mapping's fixed bindings and output extent |
| `vt0.f32`, `vt1.f32`, `vt2.f32` | Runner | Output conversion / comparator | Tightly packed float32 RGBA UAV results |
| PNG maps and material info | Bake / output converter | Model importer | Conventional colour, normal, gloss and AO assets |
| `terrain_export.json`, `inventory.json` | Bake / finalizer | Reviewer | Output metadata, limitations and hashes |

The ordinary GUI uses the same path: [capture and bake invocation](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/src/WraithXCOD/WraithXCOD/assets/CoDAssets.cpp#L2638-L2648), then model writers and finalization. Successful finalization removes scratch inputs as explained in the [capture chapter](06-capture-workflow.md#practical-reproduction-and-retention).

## Binding layout

The runner's root signature maps the saved resources as follows. Register spaces are part of the identity: `t256 space1` and `t256 space4` are different tables. [Root signature and samplers](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L148-L178).

| Binding | Resource | Extent or stride |
| --- | --- | --- |
| `t56 space6` | GPU tile structured buffer | 316 bytes per record |
| `t58 space6` | GPU layer structured buffer | 128 bytes per record |
| `t70 space6` | Weather structured buffer | 96 bytes per record; default zeros |
| `t71 space6` | Weather texture records | 32 bytes per record; default zeros |
| `t72`, `t73 space6` | Weather blend and index images | Default black placeholders |
| `t256 space1` | Float-sampled texture array | 16,384 descriptor slots |
| `t256 space4` | Integer-sampled texture array | 16,384 descriptor slots |
| `t0 space0` | Distortion image | Recovered resource in the production bake |
| `u0`, `u1`, `u2 space0` | Output images | RGBA32_FLOAT |
| `s256 space1` | Dynamic sampler array | 256 linear-wrap states |
| `b4 space0` | Generic constants | At least 256 bytes before CBV alignment |
| `b2 space0` | Scene constants | At least 2656 bytes before CBV alignment |

Structured-buffer setup is in [runner lines 89–109](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L89-L109). Native texture formats and dimensions control upload sizing; D3D12 row pitches are handled explicitly rather than assuming the upload footprint is tightly packed. [Texture creation and upload](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L59-L85).

Static samplers are linear clamp with mip zero forced at `s0 space0`, linear wrap at `s2 space0`, and linear clamp at `s12 space5`. The dynamic samplers are provisional reconstructed states. Matching texture bytes cannot compensate for different filtering, addressing, anisotropy or LOD bias.

The runner has a neutral one-pixel distortion fallback for controlled fixtures, but the production bake refuses a missing recovered distortion entry. A successful standalone runner invocation with neutral input therefore satisfies a weaker contract than the production bake. [Fallback](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L110-L135), [production gate](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L97-L102).

## Reconstructed constants and the border

The bake creates a 2656-byte zero-filled scene buffer and writes `(1,1,1,1)` at byte `159*16`. This is a constructed scene state, not a native captured cbuffer. [Scene setup](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L111-L114).

For a logical tile coordinate `(x,y)`, cell size `c` and output resolution `R`:

```text
logical_world_width = 32*c
interior_texels     = R-16
step               = 32*c/(R-16)
start              = mapping_origin + (x,y)*32*c + (0.5-8)*step
world(thread)      = start + thread.xy*step
```

The eight-texel border on each side explains the subtraction of 16 from resolution and the `0.5-8` centre offset. For `c=16` and `R=1024`, the logical tile spans 512 world units and the sampling step is approximately `0.507936508` world units. This is a derived example, not a captured constant. [Per-tile constants](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L163-L177).

The generic buffer also receives camera XY at byte 32, a float one at byte 60, and the packed values `<uint32 0, uint32 1, float32 1>` at byte 64. All remaining bytes begin as zero. These choices are part of the reference configuration and must be preserved when comparing a port.

The production bake accepts square resolutions 256, 512 or 1024; 1024 is the default. The lower-level runner accepts positive width and height divisible by eight, each no larger than 4096. It dispatches `(width/8,height/8,1)`. Those are different limits at different entry points. [Bake CLI](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L278-L285), [runner input gate](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L30-L44), [dispatch/readback](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L190-L213).

## Material output is not final lighting

The selected raw outputs are colour (`vt0.rgb`), validity (`vt0.a > 0.5`), encoded detail normal (`vt1.xy`), roughness (`vt1.z`) and ambient occlusion (`vt2.x`). The [port chapter](03-shader-port.md#output-interpretation) gives the normal decode and target adaptation.

`output_maps.py` performs a different operation from the raw-float comparator. It decodes and flips normal green for the export frame, converts roughness to gloss, fills invalid shading texels from their nearest valid neighbour, and clamps/rounds to bytes. An all-invalid input receives conventional defaults in this converter; the bake separately rejects a solid tile with no valid shading. Consequently, comparing exported PNGs cannot reproduce the raw report's metric exactly. [Output conversion](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/output_maps.py#L11-L33), [no-coverage rejection](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L228-L232).

Geometry uses a conservative four-corner solidity rule and a fixed 33 × 33 grid per tile. The packed hole mask expands a uint32 word into an 8 × 4 bit pattern. Height comes from an R16 atlas and the tile's transforms. This is a useful export representation but does not reproduce the game's adaptive LOD/morph draw topology. [Mask and geometry decode](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L48-L94).

## Commands and what they actually produce

From a correctly configured pinned Greyhound checkout, build the native runner with its [build helper](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/build.ps1#L1-L8):

```powershell
powershell -File tools/cold_war/terrain/build.ps1
```

Given an already retained **complete** focused input set:

```powershell
python tools/cold_war/terrain/bake.py '<retained-inputs>/inputs.json' --output '<new-output>' --area nearby --resolution 1024
```

This Python command writes bake intermediates and material images, leaving `terrain_export.json` at `awaiting_model_export`. The C++ caller performs the actual model export and calls the finalizer. Running the Python command alone is not a complete final model package. [Bake status and model manifest](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py#L268-L275), [model export/finalizer](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/src/WraithXCOD/WraithXCOD/assets/CoDAssets.cpp#L2649-L2697).

For one existing dispatch fixture, use the lower-level runner directly:

```powershell
tools/cold_war/terrain/run_composition.exe '<fixture>/dispatch.json'
```

The optional `--serve` mode keeps the device, shader and textures alive. It announces `ready`, accepts tab-separated generic-file/output-directory jobs, and responds with `ok`; the production baker uses it to avoid reloading resources per tile. It is an execution protocol, not a capture API. [Server protocol](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp#L215-L237).

Keep archived source evidence immutable. Copy inputs to a separate experiment directory before running the baker: it writes scene/generic/dispatch files alongside its input manifest. Preserve the copied paths or deliberately rebase them, because the focused capture writes path strings tied to its capture location. Verify shader and resource hashes before comparing results.

## A useful fidelity boundary

This pipeline establishes the supported program's output for a specified collection of inputs. It combines captured shader/native resource bytes with reconstructed dispatch state and conventional export geometry. It excludes full native sampler recovery, synchronized weather state, independent volume decals, collision and final lighting. The study's port comparison is therefore an experiment against this reference, while the [controlled equation experiments](08-shader-experiments.md) isolate particular operations within the supported shader.
