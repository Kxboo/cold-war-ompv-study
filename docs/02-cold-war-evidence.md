# Cold War capture evidence

## Surface resources

An earlier capture audit found five index/colour/control triplets across four captures. Binding numbers belong to each capture, not to a universal engine register layout.

| Capture | Surface | Index binding | Colour binding | Coarse control binding |
| --- | ---: | ---: | ---: | ---: |
| 4a22-fresh | 0 | 11 | 12 | 13 |
| 4d94-fresh | 0 | 18 | 19 | 20 |
| d7b5-fresh | 0 | 30 | 31 | 32 |
| d7b5-fresh | 1 | 246 | 247 | 248 |
| eec1-fresh | 0 | 12 | 13 | 14 |

The audit records 2048 × 2048 index and colour images with one mip. The index format is R8_UINT (DXGI 62); the adjacent colour format is BC7_UNORM (98). The neighbouring 257 × 257 R32_UINT (42) grids have a different resolution. They cannot serve as the same-footprint RGB input without an additional transformation. The exact binding sequence is an observed discovery heuristic, not a guarantee for every capture. [Evidence and hashes](../evidence/capture-summary.json).

These observations qualify two common assumptions. The 2023 presentation's BC1 colour example does not establish the format in every Cold War capture. Likewise, a nearby packed integer control grid is not automatically a colour-ramp mask. Format, resolution and actual shader use need to agree.

## Colour evidence has several levels

The GDC 2021 colour-ramp explanation and the later RGB-map explanation are related descriptions, but they do not establish one universal application formula. The earlier research found transferable within-material colour variation in a held-out fit. That fit removed a per-material constant, so it did not recover the absolute tint multiplier.

A separate scan did not observe `rColorRamp` across 22, 38, 35 and 4 slot-referenced materials in the four fresh captures. This scopes the observation to those materials. It does not prove that an uncaptured permutation lacks that semantic. [Local audit provenance](05-sources.md#local-research-provenance).

## Why source-material shaders were insufficient

The earlier shader trace covered 512 references representing 128 unique DXIL binaries. Its material-pool entries did not bind the defining map-wide TerrainGfx resources. These were source-layer techniques, so their existence could not prove the renderer-owned OMPV gather and composition sequence.

The later work obtained the composition shader and used it through Greyhound's saved-input bake. The supported binary SHA-256 is:

```text
6159daeb7882198314ffe9e8b6fab53c1b314258b43a106c1694c5a53d77d9ff
```

Greyhound's bake verifies that hash and requires the recovered distortion input. Its runner binds the saved resources and dispatches the original bytecode on D3D12 WARP. This gives the HLSL experiment a concrete reference output. [Pinned bake and runner](05-sources.md#greyhound-reference).

## What the reference bake establishes

The bake executes the actual supported composition bytecode with its provided inputs. Its own limitations include reconstructed dispatch constants, provisional linear-wrap bindless samplers, omitted weather globals, and omission of independent volume decals. Its geometry export also uses a static logical grid and a conventional normal adaptation.

Consequently, close agreement with that bake demonstrates agreement with **that reference configuration**. It does not prove that a complete in-game frame, all weather states, or all rendering passes match. A captured shader hash establishes bytecode identity, not the correctness of every bound input. [Greyhound bake limitations](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py).

## Geometry and BO4 are separate questions

CPU tile records, GPU composition records and material records are different layouts. The port interface uses 316-byte GPU tile records and 128-byte layer records; those sizes must not be substituted for the native CPU geometry layout.

The BO4 research follows a different representation involving layer weight arrays. The Cold War shader hash and resource assumptions do not establish BO4 compatibility. Likewise, importing a composed material into BO3 requires separate geometry, coordinate-origin, G-buffer, texture and collision work. The study's material metrics measure none of those geometry or gameplay properties.
