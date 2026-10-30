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
- [Focused composition capture](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/src/WraithXCOD/WraithXCOD/games/cold_war/terrain/CWTerrainBake.h): supported PE layout, paired process reads, native image extraction, composition globals and saved input manifest.
- [Finalizer](https://github.com/Kxboo/Greyhound/blob/2f3d1020ede04602759d5eb68405df519ec8221b/tools/cold_war/terrain/finalize.py): validation and removal of successful-export scratch data.

The [capture workflow](06-capture-workflow.md) and [replay contract](07-replay-contract.md) cite exact line ranges. [greyhound-source-map.json](../evidence/greyhound-source-map.json) records SHA-256 hashes of 11 exact Git blobs and 40 cited excerpts. Verify those references against a clone containing the pinned commit:

```console
python tools/verify_greyhound_sources.py --greyhound PATH_TO_GREYHOUND
```

The check reads `git show COMMIT:path`, not the current working-tree files. It proves that the inspected source and line ranges are unchanged; it does not independently validate their behavior or the prose's interpretation.

Greyhound is GPL-3.0 licensed. Its code is referenced here; no Greyhound source has been relicensed into the educational example.

## Local research provenance

The study was prepared from the existing TerrainReconstructor research working tree. Several source files had uncommitted changes; a repository commit alone would not identify the inspected versions. [provenance.json](../evidence/provenance.json) therefore records file-content SHA-256 hashes using portable logical names.

The inspected evidence includes the earlier fresh-capture correlation, colour holdout and material-shader trace; the OMPV Python helpers; the later DXIL translator and resource interface; the validation harness and comparator; the BO3 handoff notes; and the saved native-atlas comparison report. The public [capture-summary.json](../evidence/capture-summary.json) selects numerical facts from the earlier audit. The saved [shader-validation.json](../evidence/shader-validation.json) preserves the existing report with only CRLF line endings normalized to LF. Provenance records separate hashes for the source and published file.

The source hashes make the inspected versions identifiable. They do not make unavailable captures publicly reproducible or authenticate an entire rendering run. This publication records existing research and validates the new educational examples; it does not claim a fresh game capture or fresh WARP replay.

The expanded [shader-experiments.json](../evidence/shader-experiments.json) has a separate `source_files` manifest for 12 historical composition reports, validators, trace scripts and research notes. Its numerical fields retain their source report names and JSON pointers where applicable. The [experiments chapter](08-shader-experiments.md) distinguishes that local historical evidence from the public production code and from the examples included here. Absolute process addresses and machine-specific paths are omitted from the portable extract.

## Interpretation rules

- **Documented mechanism:** supported by the primary presentations.
- **Captured observation:** supported by the named capture audit, within its maps and surfaces.
- **Port implementation:** supported by the inspected local translator/interface, with explicit substitutions.
- **Saved measurement:** a value in the published historical comparison report.
- **Illustration or proposal:** synthetic example, teaching shader, or suggested next experiment.

These levels prevent a plausible reconstruction, a public algorithm description and a captured runtime fact from being treated as equivalent evidence.
