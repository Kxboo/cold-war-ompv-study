# Surface sounds, seamless shading and collision

The zm_silver terrain now uses **Cold War’s captured collision surface map to select surface-appropriate footsteps and impacts in BO3**. Snow, rock, dirt, ice, mud and concrete each use a variant of the same terrain material. The visual blend continues to run through the translated Cold War composition shader.

This is a surface-category mapping into BO3’s responses. It does not establish that Cold War audio recordings were imported or that the two games play identical audio. In-game footstep agreement is reported in the supplied handoff; the checks below measure the captured categories, installed materials and generated geometry.

## One visual shader across seven materials

The base material is `superterrain_cw_zm_silver`. Six copies add the suffixes `snow`, `rock`, `dirt`, `ice`, `mud` and `concrete`. Inspection of the installed GDT entries found **the same 25 keys except for `surfaceType`**; the snow copy even retains the base’s surface value. All seven share the techset, images, data tables and origin XY **(-812, 57)**.

The pixel shader derives its sampling position from world XY minus that origin. The material’s surface category does not select a different colour blend. Adjacent snow and rock patches therefore use the same composition inputs at a shared position. The surface split controls physical responses while preserving the continuous material calculation.

Changing only `surfaceType` preserves those shader inputs. The later terrain rebuild also changed tessellation and detail allocation, so the earlier **99.96% one-tile colour result is not a fresh measurement of this complete surface-split build**. The [validation chapter](04-validation.md) keeps shader-output, geometry and sound claims separate.

## The surface map comes from collision

Cold War stores these categories in its CLIP_MAP terrain heightfield, separately from the visible OMPV layer blend. A snowy-looking pixel can legitimately be rock underfoot. Selecting the strongest visible material would lose that distinction.

The inspected decoder reads a **1025 × 1025** slot grid at **16 world units per sample**, aligned from XY **(-8192, -8192)**. Its 44 collision-layer records are **24 bytes each**, with `surfaceFlags` at byte 8; the surface code is `(surfaceFlags >> 20) & 0x3f`. These are a different record structure from the render shader’s 128-byte layer records. All **44 captured flags words matched their associated material header’s flags word** at byte 32.

The retained capture contains six used categories. Rounded source shares are snow 75.7%, rock 19.2%, dirt 3.6%, ice 0.9%, mud 0.4% and concrete 0.3%. Rounding means these percentages need not sum to exactly 100%.

The decoder’s module-relative addresses describe the inspected game build. They require revalidation for another executable version; the declaration names and record stride must not be inferred from a different game’s layout.

## How accurately the patches retain those surfaces

Each 16- or 32-unit lattice cell takes the majority captured surface among its source samples. Contiguous cells of one category become rectangular patches. Their vertices retain the visible terrain’s heights.

The current `cw_surface_nav_zm_silver` prefab matches **58,168 of 62,227 covered, labelled source samples: 93.48%**. This denominator is the source samples beneath typed surface patches, not the entire map or the number of footsteps played. Most disagreement occurs at boundaries where a coarser cell spans multiple categories.

| Current prefab check | Result |
| --- | ---: |
| Visible colliding surface patches | 4,097 |
| Shared vertex coordinates checked | 34,593 |
| Largest shared-vertex height disagreement | 0 |
| Drawn cells covered more than once | 0 |
| Visible controls | 497,653 |
| Surface-patch collision triangles | 51,600 |
| Additional coarse-floor triangles | 7,850 |
| Total collision triangles | 59,450 |

These are fresh file inspections of the retained current prefab, not a new game playtest. The [surface evidence summary](../evidence/surface-sounds.json) records the checks and source fingerprints. They supersede the intermediate invisible-collision build’s counts in the handoff.

## Why the visible patches also collide

An intermediate version used non-colliding visible terrain over a separate invisible surface-typed collision layer. Footstep selection worked, but the tested BO3 navmesh build omitted the terrain. In the controlled comparison, invisible `noDraw` collision supplied only 12 navmesh-input triangles from the test floor; visible shader-material collision supplied 49,766 including the terrain.

The final fix makes the visible, surface-typed patches collide in the playable area. The handoff records full-map navmesh input rising from **102,222 to 153,822 triangles**: the added **51,600** matches the surface-patch triangles. Nodes that could not drop fell from 29 to 21, and bad nodes at link fell from 58 to 39. Remaining nodes over holes or above the ground still require placement work. Those compile figures are retained handoff observations, not new compiles performed for this study.

Outside the playable area, the base material remains visual-only and a coarse invisible floor supplies limited collision. The surface split adds boundary vertices and more patches; it does not add triangles to an otherwise unchanged cell lattice. The current builder budgets collision in triangles. The old 28,800-control policy was a project policy, not an established BO3 engine limit.

## Editing or moving the terrain

| Change | Required action |
| --- | --- |
| Move the terrain in XY | Update `cg00_x` and `cg00_y` on **all seven materials**, or regenerate them with the new origin. |
| Change a shared image or shader setting | Edit the base entry and regenerate the six copies, or apply the identical change to each. |
| Correct a local ground response | Assign the patch another surface variant; its visual shader inputs remain the same. |
| Rebuild navigation | Compile from BO3’s `bin` directory with the intended `-navmesh -navvolume` settings, then link once. Verify that terrain triangles enter the navmesh. |

This chapter is based on the supplied `CW_TERRAIN_SURFACES_AND_BLENDING_BO3.md` and `CW_TERRAIN_SURFACE_TYPES_BO3_HANDOFF_2026_10_30.md`, checked against the decoder, builder and retained installed files. Their hashes are recorded in the evidence summary. The complete integration and game resources remain external to this study.
