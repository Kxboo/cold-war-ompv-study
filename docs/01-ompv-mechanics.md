# OMPV mechanics

## What one material per vertex means

OMPV's name refers to the authoring samples. The index image stores one layer ID per texel, while a shading location can receive contributions from four neighbouring samples. It therefore does not imply one material per rendered triangle or one material evaluation per output pixel. The 2021 deck makes the distinction explicit in slides 96–99. [Source: GDC 2021](05-sources.md#primary-presentations).

A layer ID is categorical. Linear interpolation between IDs 2 and 8 cannot identify a meaningful material 5. Instead, gather the integer IDs and compute weights for their locations. Repeated IDs share one material evaluation after their weights have been combined.

```mermaid
flowchart LR
    A[World position] --> B[Control-map coordinates]
    B --> C[Shared coordinate distortion]
    C --> D[Gather four IDs and colour controls]
    D --> E[Combine duplicate IDs]
    E --> F[Order distinct layers]
    F --> G[Evaluate source materials and reveal]
    G --> H[Composed material channels]
```

This diagram describes material composition. VT page addressing, streaming, final lighting, and terrain geometry are separate systems.

## Coordinates and weights

The reference example uses texel-centre coordinates. For normalized coordinates `(u,v)` and dimensions `(W,H)`:

```text
p = (u*W - 0.5, v*H - 0.5)
b = floor(p)
f = p - b
```

Load the four integer neighbours in the explicit order **top-left, top-right, bottom-left, bottom-right**. With `f=(x,y)`, their coverage weights are:

```text
[(1-x)*(1-y), x*(1-y), (1-x)*y, x*y]
```

At `p=(0.25,0.75)`, the weights are `[0.1875, 0.0625, 0.5625, 0.1875]`. They are nonnegative and sum to one. The example clamps individual coordinates at the image edge; it does not wrap the whole control map.

This array order is a software convention. Hardware `Gather` component order must be mapped to the matching weights. Copying a slide's `float4` into a differently ordered four-load implementation rotates the contributions. [GDC slides 123–124](05-sources.md#primary-presentations); [executable reference](../examples/ompv_reference.py).

## Combine duplicates and keep colour attached to its layer

Consider a synthetic 2 × 2 cell:

```text
7  7
2  7
```

Using the weights above, material 7 receives `0.4375`; material 2 receives `0.5625`. The numerical ordering is then `[2,7]`. No material 3, 4, 5 or 6 is created by filtering.

For colour controls `c_i`, carry the premultiplied sum for each material `m`:

```text
A_m = sum(w_i                 for i where id_i == m)
C_m = sum(w_i * c_i           for i where id_i == m)
mean_control_m = C_m / A_m    when A_m > 0
```

The accumulator `C_m` and normalized mean are different quantities. The teaching model returns both. It uses the mean as a synthetic tint for illustration; that choice is not a recovered Cold War colour transform. Globally filtering colour first mixes controls that belong to different materials. Slide 126 motivates carrying colour through duplicate combination. [GDC 2021](05-sources.md#primary-presentations).

The example accepts all IDs `0…255`. It uses an explicit count instead of reserving byte 255 as an invalid layer. Some earlier research helpers use 255 as an internal sentinel; that convention must not silently reduce a format's representable range.

At exact sample boundaries, the teaching model drops zero-weight materials before choosing its base, which also keeps its normalized colour control defined. The inspected captured variant retains the gathered ID list and can use its lowest ID as the opaque base even when that ID has zero weight. Its internal exhausted-entry sentinel is 256. See [the controlled selection experiment](08-shader-experiments.md#isolating-selection-and-duplicate-combination). The browser's observed-reveal mode changes the scalar reveal equation while retaining the teaching model's selection and colour conventions.

## Reveal ordering and coverage

The public presentations prescribe numeric layer ordering. The minimum participating ID supplies the primary layer, with full base coverage. Subsequent layers are blended in order. A list of recovered material sort keys is not sufficient reason to replace this rule. [GDC slides 109, 123–125](05-sources.md#primary-presentations); [SIGGRAPH notes, PDF pages 9–10](05-sources.md#primary-presentations).

The example uses this **illustrative** reveal rule for non-primary layers:

```text
alpha = clamp(2 * coverage - 1 + reveal, 0, 1)
result = (1-alpha) * result + alpha * layer_colour
```

It is based on the painted/rules-alpha relation on GDC slide 49 and the doubled-alpha discussion on slide 109. It is not a complete implementation of Cold War's captured composition shader. That shader includes additional material parameters and branches. Bilinear coverage, effective reveal alpha and sequential compositing weights must be reported separately.

The [observed reveal equation](08-shader-experiments.md#the-observed-reveal-equation) describes the separately tested width/exponent shaping, endpoint correction and zero-width behavior for the supported binary. Keeping the two equations visibly separate makes it possible to experiment without mistaking an illustration for an engine implementation.

## Distortion, material UVs and GPU execution

The 2023 explanation describes a shared 256 × 256 noise texture that perturbs coordinates before both the index and colour lookups; amplitude and frequency are level settings. This is distinct from source-material UV scale, tile-hiding rotations, or Vista UV sampling. A synthetic noise field can demonstrate distortion, but cannot establish the game's captured texture or constants. [SIGGRAPH 2023, PDF page 11](05-sources.md#primary-presentations).

On a GPU, neighbouring lanes can select different materials. GDC slide 125 describes coordinating which layer lanes process to handle sampler divergence. The small reference shader uses synthetic array-backed material values and demonstrates the arithmetic only; it does not reproduce that wave-level execution strategy. An upper bound of four unique gathered IDs is not a bound of four texture fetches for the full material shader.
