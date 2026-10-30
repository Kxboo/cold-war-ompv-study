/** Original, synthetic OMPV arithmetic. No game resources or engine dependencies. */
export const CORNERS = ['TL', 'TR', 'BL', 'BR'];
export const clamp = (value, low = 0, high = 1) => Math.min(high, Math.max(low, value));

export function gather(indexMap, uv, controls = null) {
  const height = indexMap.length;
  const width = height ? indexMap[0].length : 0;
  if (!width || indexMap.some(row => row.length !== width)) {
    throw new RangeError('The index map must be a nonempty rectangular grid.');
  }
  if (indexMap.some(row => row.some(id => !Number.isInteger(id) || id < 0 || id > 255))) {
    throw new RangeError('All material IDs must be integers from 0 through 255.');
  }
  if (uv.length !== 2 || !uv.every(Number.isFinite)) {
    throw new RangeError('UV must contain two finite values.');
  }
  if (controls && (controls.length !== height || controls.some(row => row.length !== width)
      || controls.some(row => row.some(rgb => rgb.length !== 3 || !rgb.every(Number.isFinite))))) {
    throw new RangeError('Controls must match the index map and contain finite RGB triples.');
  }
  const p = uv.map((coordinate, axis) => coordinate * [width, height][axis] - 0.5);
  const base = p.map(Math.floor);
  const f = p.map((coordinate, axis) => coordinate - base[axis]);
  const [x, y] = f;
  const weights = [(1 - x) * (1 - y), x * (1 - y), (1 - x) * y, x * y];
  return [[0, 0], [1, 0], [0, 1], [1, 1]].map(([dx, dy], index) => {
    const cx = clamp(base[0] + dx, 0, width - 1);
    const cy = clamp(base[1] + dy, 0, height - 1);
    return { material: indexMap[cy][cx], weight: weights[index],
      control: controls ? [...controls[cy][cx]] : [1, 1, 1],
      corner: CORNERS[index], texel: [cx, cy] };
  });
}

export function combine(samples) {
  // Teaching convention: omit zero weights. The captured variant can retain
  // a zero-weight lowest gathered ID as the opaque base (chapter 08).
  const entries = new Map();
  for (const [sampleIndex, { material, weight, control }] of samples.entries()) {
    if (weight <= 0) continue;
    if (!entries.has(material)) entries.set(material, {
      material, coverage: 0, weighted_control: [0, 0, 0], corners: [],
    });
    const entry = entries.get(material);
    entry.coverage += weight;
    entry.weighted_control = entry.weighted_control.map((value, channel) => value + weight * control[channel]);
    entry.corners.push(sampleIndex);
  }
  return [...entries.values()].sort((a, b) => a.material - b.material).map(entry => ({
    ...entry, mean_control: entry.weighted_control.map(value => value / entry.coverage),
  }));
}

export function revealAlpha(coverage, reveal) {
  return clamp(2 * coverage - 1 + reveal);
}

/** Equation isolated from the supported variant; not a complete shader implementation.
 * Coverage is the merged bilinear weight. Width/exponent represent bytes 82/83 / 255.
 * The saturate of a NaN from a degenerate interval is modeled as zero.
 */
export function observedReveal(coverage, sample, width = 128 / 255, exponent = 128 / 255) {
  if (coverage <= 0) return { coverage: 0, low: 1, high: 1, raw: 0, endpoint: 0, alpha: 0 };
  const doubled = clamp(2 * coverage);
  const c = clamp(0.998 * doubled + 0.001);
  const inv = 1 - c;
  const low = clamp(inv - clamp(width) * c ** clamp(exponent));
  const high = clamp(inv + clamp(width) * inv ** clamp(exponent));
  const quotient = (sample - low) / (high - low);
  const raw = Number.isNaN(quotient) ? 0 : clamp(quotient);
  const endpoint = clamp((doubled - 0.99) * 100);
  return { coverage: doubled, low, high, raw, endpoint, alpha: Math.max(raw, endpoint) };
}

export function traceComposite(contributions, materials, mode = 'teaching') {
  if (!contributions.length) throw new RangeError('At least one contribution is required.');
  let colour = [0, 0, 0];
  const layers = [...contributions].sort((a, b) => a.material - b.material).map((entry, index) => {
    const material = materials[entry.material];
    if (!material) throw new RangeError(`Missing material ${entry.material}.`);
    const layerColour = material.colour.map((value, channel) => value * entry.mean_control[channel]);
    const reveal = observedReveal(entry.coverage, material.reveal, material.width, material.exponent);
    const alpha = index === 0 ? 1 : mode === 'observed' ? reveal.alpha : revealAlpha(entry.coverage, material.reveal);
    colour = colour.map((old, channel) => (1 - alpha) * old + alpha * layerColour[channel]);
    return { ...entry, alpha, primary: index === 0, layerColour, after: [...colour], reveal };
  });
  let remaining = 1;
  for (let index = layers.length - 1; index >= 0; index -= 1) {
    layers[index].finalWeight = layers[index].alpha * remaining;
    remaining *= 1 - layers[index].alpha;
  }
  return { colour, layers };
}

export function composite(contributions, materialColours, revealValues) {
  const materials = Object.fromEntries(Object.entries(materialColours).map(([id, colour]) => [id, {
    colour, reveal: revealValues[id],
  }]));
  return traceComposite(contributions, materials).colour;
}

export function srgbToLinear(value) {
  return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}

export function linearToSrgb(value) {
  value = clamp(value);
  return value <= 0.0031308 ? 12.92 * value : 1.055 * value ** (1 / 2.4) - 0.055;
}

export function toCss(colour) {
  return `rgb(${colour.map(value => Math.round(linearToSrgb(value) * 255)).join(' ')})`;
}

export function materialColour(id) {
  // Stable, synthetic palette; material IDs do not encode a real-world surface type.
  const palette = [[0.19, 0.32, 0.22], [0.52, 0.29, 0.12], [0.25, 0.38, 0.48],
    [0.61, 0.49, 0.23], [0.38, 0.22, 0.27], [0.35, 0.40, 0.29], [0.47, 0.29, 0.19],
    [0.63, 0.36, 0.15]];
  return [...palette[id % palette.length]];
}
