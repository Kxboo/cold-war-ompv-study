# Sources and provenance

## Primary presentations

1. **J.T. Hooker, GDC 2021, Boots on the Ground: The Terrain of Call of Duty.** [Activision Research publication](https://research.activision.com/publications/2021/09/boots-on-the-ground--the-terrain-of-call-of-duty), [official PowerPoint](https://www.activision.com/cdn/research/GDC21_Terrain_of_CoD.pptx). Relevant slides: 49 (painted/rules alpha), 94–113 (OMPV and reveal), 114–127 (colour control and manual filtering), 155–157 (Cold War terrain and virtual texturing). The locally available deck was inspected directly for the algorithm passages. The presentation remains owned by its publisher and is linked rather than redistributed.
2. **Stephane Etienne, SIGGRAPH 2023, Large Scale Terrain Rendering in Call of Duty.** [Official course](https://advances.realtimerendering.com/s2023/index.html), [PDF with speaker notes](https://advances.realtimerendering.com/s2023/Etienne%28ATVI%29-Large%20Scale%20Terrain%20Rendering%20with%20notes%20%28Advances%202023%29.pdf). One-based PDF pages 8–10 explain OMPV; page 11 explains distortion. Printed slide numbers and PDF page indices differ. This later talk is useful context, not proof that every later AVT detail applies unchanged to Cold War.

## Greyhound reference

Public source is pinned to commit `2f3d1020ede04602759d5eb68405df519ec8221b`:

- [Terrain discovery and decoding](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/docs/cw-terrain.md).
- [Saved-input reference bake](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/bake.py): supported binary hash, required distortion, dispatch preparation and limitations.
- [D3D12 WARP runner](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/run_composition.cpp): descriptors, resources and execution.
- [Output conversion](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/output_maps.py): normal decode, validity and conventional maps.
- [Capture code](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/src/WraithXCOD/WraithXCOD/assets/CoDAssets.cpp): OMPV correlations and captured resources.

Greyhound is GPL-3.0 licensed. Its code is referenced here; no Greyhound source has been relicensed into the educational example.

## Local research provenance

The study was prepared from the existing TerrainReconstructor research working tree. Several source files had uncommitted changes; a repository commit alone would not identify the inspected versions. [provenance.json](../evidence/provenance.json) therefore records file-content SHA-256 hashes using portable logical names.

The inspected evidence includes the earlier fresh-capture correlation, colour holdout and material-shader trace; the OMPV Python helpers; the later DXIL translator and resource interface; the validation harness and comparator; the BO3 handoff notes; and the saved native-atlas comparison report. The public [capture-summary.json](../evidence/capture-summary.json) selects numerical facts from the earlier audit. The saved [shader-validation.json](../evidence/shader-validation.json) preserves the existing report with only CRLF line endings normalized to LF. Provenance records separate hashes for the source and published file.

The source hashes make the inspected versions identifiable. They do not make unavailable captures publicly reproducible or authenticate an entire rendering run. This publication records existing research and validates the new educational examples; it does not claim a fresh game capture or fresh WARP replay.

## Interpretation rules

- **Documented mechanism:** supported by the primary presentations.
- **Captured observation:** supported by the named capture audit, within its maps and surfaces.
- **Port implementation:** supported by the inspected local translator/interface, with explicit substitutions.
- **Saved measurement:** a value in the published historical comparison report.
- **Illustration or proposal:** synthetic example, teaching shader, or suggested next experiment.

These levels prevent a plausible reconstruction, a public algorithm description and a captured runtime fact from being treated as equivalent evidence.
