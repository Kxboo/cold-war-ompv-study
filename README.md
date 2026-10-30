# Cold War OMPV shader study

A technical study of **One Material Per Vertex (OMPV)** terrain composition in **Call of Duty: Black Ops Cold War**, by Kxboo / SuperTerrain contributors. Published October 29, 2026.

OMPV stores a material ID at each control-map texel. Shading gathers four IDs, combines repeated materials, and evaluates the resulting layers in order. Reveal maps shape the transitions. This compact representation is an input to material composition; virtual texturing handles storage and reuse of the composed result.

The study connects the public terrain presentations to Cold War capture observations and a later DXIL-to-HLSL port experiment. Its strongest numerical result is a saved **1024 × 1024 atlas-backed comparison against Greyhound's reference bake**: colour MAE **0.113/255** and validity agreement **100%**. This is one tile under the bake's reconstructed inputs, provisional samplers, and omitted weather globals. It does not establish full-frame or all-map equivalence.

![Synthetic OMPV gathering and duplicate combination](assets/ompv-gather.svg)

## Read the study

| Topic | Contents |
| --- | --- |
| [OMPV mechanics](docs/01-ompv-mechanics.md) | Coordinate convention, integer gathering, bilinear coverage, duplicate combination, colour controls, ordering and reveal |
| [Cold War evidence](docs/02-cold-war-evidence.md) | Captured formats, surface-local bindings, the earlier material-shader dead end, and the renderer-owned composition path |
| [Shader port](docs/03-shader-port.md) | Compute-to-pixel adaptation, resource repacking, derivatives, output channels and exactness limits |
| [Validation and reproduction](docs/04-validation.md) | Exact saved metrics, failure cases, synthetic checks and comparison of user-supplied outputs |
| [Sources and provenance](docs/05-sources.md) | Primary presentations, pinned Greyhound source and hashes of the local research evidence |

## Run the example

The educational model uses Python 3.10+ and only the standard library:

```console
python examples/ompv_reference.py
python -m unittest discover -s tests -v
python tools/make_diagram.py
```

The example prints the four gathered IDs and weights, followed by their combined contributions. Its synthetic grid contains no game assets. [The HLSL companion](shaders/ompv_reference.hlsl) implements the same gather/combine and illustrative reveal operations as a self-contained compute example. It is a teaching implementation, not the recovered Cold War shader.

For comparison of existing shader output files, install NumPy with `python -m pip install -r requirements-analysis.txt`, then follow the [validation instructions](docs/04-validation.md).

## Research status

**Established in scope:** the public OMPV mechanism, repeated index/colour/control patterns in four earlier captures, the reference bake's shader identity, the port's documented substitutions, and the saved per-channel comparison.

**Still open:** unexplained outliers, coverage across maps and shader permutations, exact captured-frame resource state, behaviour with weather/decal passes, and equivalence at distant pixel footprints. The RGB control's absolute application cannot be inferred from a successful colour-correlation fit alone.

The repository contains original explanations, synthetic examples and selected numerical evidence. Captured textures, shader binaries/disassembly, game maps, and the full BO3 integration remain external inputs. The earlier Python reconstruction tools and the later shader port are distinct experiments; their results are not interchangeable.

## Credits

The terrain design is described by J.T. Hooker's [GDC 2021 presentation](https://research.activision.com/publications/2021/09/boots-on-the-ground--the-terrain-of-call-of-duty) and Stephane Etienne's [SIGGRAPH 2023 presentation](https://advances.realtimerendering.com/s2023/index.html). Capture and reference baking use [Kxboo/Greyhound](https://github.com/Kxboo/Greyhound), based on Scobalula's Greyhound and Wraith Archon. See [NOTICE.md](NOTICE.md) for attribution and scope of the [MIT license](LICENSE).
