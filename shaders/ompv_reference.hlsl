// Educational OMPV model. Original synthetic code, not recovered game HLSL.
// cs_5_0 / entry cs_main. Controls and material colours are linear values.
// t0: R8_UINT material IDs, t1: matching RGB control image.
// t2: 256 float4 records: synthetic material RGB + reveal scalar in W.
// u0: float4 output image; b0: output dimensions and two padding uints.
// UV covers the index grid, clamped at edges. All IDs 0..255 are legal.
// No distortion, source textures, wave coordination, VT, or normal outputs.
// Teaching selection drops zero-weight IDs. The captured variant can retain
// a zero-weight lowest gathered ID as its base (see docs/08-shader-experiments.md).
Texture2D<uint> IndexMap : register(t0);
Texture2D<float4> Controls : register(t1);
StructuredBuffer<float4> Materials : register(t2);
RWTexture2D<float4> Output : register(u0);
cbuffer Params : register(b0) { uint2 OutputSize; uint2 Padding; };

[numthreads(8, 8, 1)]
void cs_main(uint3 thread : SV_DispatchThreadID)
{
    if (any(thread.xy >= OutputSize)) return;
    uint width, height;
    IndexMap.GetDimensions(width, height);
    float2 uv = (float2(thread.xy) + 0.5) / float2(OutputSize);
    float2 p = uv * float2(width, height) - 0.5;
    int2 base = (int2)floor(p);
    float2 f = frac(p);
    float weights[4] = {
        (1-f.x)*(1-f.y), f.x*(1-f.y), (1-f.x)*f.y, f.x*f.y
    };
    int2 offsets[4] = {int2(0,0), int2(1,0), int2(0,1), int2(1,1)};
    uint ids[4] = {0, 0, 0, 0};
    float coverage[4] = {0, 0, 0, 0};
    float3 weightedControl[4] = {
        float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0)
    };
    uint count = 0;
    [unroll] for (uint corner = 0; corner < 4; ++corner)
    {
        if (weights[corner] <= 0) continue;
        int2 xy = clamp(base + offsets[corner], int2(0,0), int2(width-1, height-1));
        uint id = IndexMap.Load(int3(xy, 0));
        float3 control = Controls.Load(int3(xy, 0)).rgb;
        uint slot = count;
        [unroll] for (uint j = 0; j < 4; ++j)
            if (j < count && ids[j] == id) slot = j;
        if (slot == count) { ids[count] = id; ++count; }
        coverage[slot] += weights[corner];
        weightedControl[slot] += weights[corner] * control;
    }
    [loop] for (uint i = 0; i < count; ++i)
    {
        [loop] for (uint j = i+1; j < count; ++j)
        {
            if (ids[j] < ids[i])
            {
                uint id = ids[i]; ids[i] = ids[j]; ids[j] = id;
                float a = coverage[i]; coverage[i] = coverage[j]; coverage[j] = a;
                float3 c = weightedControl[i]; weightedControl[i] = weightedControl[j]; weightedControl[j] = c;
            }
        }
    }
    float3 result = 0;
    [loop] for (uint layer = 0; layer < count; ++layer)
    {
        float4 material = Materials[ids[layer]];
        float3 tint = weightedControl[layer] / coverage[layer];
        float alpha = layer == 0 ? 1.0 : saturate(2*coverage[layer] - 1 + material.w);
        result = lerp(result, material.rgb * tint, alpha);
    }
    Output[thread.xy] = float4(result, 1);
}
