import test from 'node:test';
import assert from 'node:assert/strict';
import { combine, gather, observedReveal, traceComposite, linearToSrgb, srgbToLinear } from '../site/ompv-model.mjs';

const near = (actual, expected, epsilon = 1e-12) => assert.ok(Math.abs(actual - expected) < epsilon, `${actual} != ${expected}`);

test('gather rejects non-categorical IDs and invalid coordinates', () => {
  for (const grid of [[], [[1], [1, 2]], [[256]], [[-1]], [[1.5]], [[NaN]]]) assert.throws(() => gather(grid, [.5, .5]));
  assert.throws(() => gather([[1]], [NaN, .5]));
  assert.throws(() => gather([[1]], [.5, .5], []));
});

test('all 256 byte IDs survive gather and combination without a sentinel collision', () => {
  for (let id = 0; id < 256; id += 1) {
    const [entry] = combine(gather([[id]], [.5, .5]));
    assert.equal(entry.material, id);
    assert.equal(entry.coverage, 1);
  }
});

test('repeated material retains all and only its associated RGB controls', () => {
  const entries = combine(gather([[7, 7], [2, 7]], [.375, .625], [[[1, 0, 0], [0, 1, 0]], [[0, 0, 1], [1, 1, 1]]]));
  assert.deepEqual(entries.map(entry => entry.material), [2, 7]);
  assert.deepEqual(entries[0].mean_control, [0, 0, 1]);
  assert.deepEqual(entries[1].weighted_control, [.375, .25, .1875]);
  assert.deepEqual(entries[1].corners, [0, 1, 3]);
  near(entries[1].mean_control[0], 6 / 7);
});

test('ordered alpha trace produces final weights that reconstruct the composite', () => {
  const entries = combine(gather([[12, 3], [255, 7]], [.5, .5]));
  const materials = { 3: { colour: [1, 0, 0], reveal: .9 }, 7: { colour: [0, 1, 0], reveal: .8 },
    12: { colour: [0, 0, 1], reveal: .9 }, 255: { colour: [1, 1, 1], reveal: 1 } };
  const trace = traceComposite(entries, materials);
  assert.deepEqual(trace.layers.map(layer => layer.material), [3, 7, 12, 255]);
  near(trace.layers[0].alpha, 1);
  near(trace.layers.reduce((sum, layer) => sum + layer.finalWeight, 0), 1);
  for (let channel = 0; channel < 3; channel += 1) {
    near(trace.layers.reduce((sum, layer) => sum + layer.finalWeight * layer.layerColour[channel], 0), trace.colour[channel]);
  }
});

test('observed reveal excludes zero coverage before its endpoint and sample rule', () => {
  assert.equal(observedReveal(0, 1, 0, 0).alpha, 0);
  assert.equal(observedReveal(-1, 1, 0, 0).alpha, 0);
});

test('observed degenerate interval handles equal, greater and lower samples', () => {
  // A=.25 -> doubled=.5 -> c=.5 -> lo=hi=.5 for width=0.
  const equal = observedReveal(.25, .5, 0, 128 / 255);
  assert.equal(equal.low, .5);
  assert.equal(equal.high, .5);
  assert.equal(equal.raw, 0); // 0/0 -> saturate(NaN) -> 0
  assert.equal(equal.alpha, 0);
  assert.equal(observedReveal(.25, .50001, 0, 0).alpha, 1);
  assert.equal(observedReveal(.25, .49999, 0, 1).alpha, 0);
});

test('observed endpoint remains opaque even when the raw reveal result is zero', () => {
  const output = observedReveal(.5, 0, 0, 0);
  assert.equal(output.raw, 0);
  assert.equal(output.endpoint, 1);
  assert.equal(output.alpha, 1);
  const halfway = observedReveal(.4975, 0, 0, 0);
  near(halfway.endpoint, .5);
});

test('observed primary layer is opaque and the later layer uses doubled coverage', () => {
  const entries = combine(gather([[7, 7], [2, 7]], [.375, .625]));
  const trace = traceComposite(entries, { 2: { colour: [0, 0, 1], reveal: 0 }, 7: { colour: [1, 0, 0], reveal: .5 } }, 'observed');
  assert.equal(trace.layers[0].alpha, 1);
  near(trace.layers[1].reveal.coverage, .875);
  assert.equal(trace.layers[1].alpha, trace.layers[1].reveal.alpha);
});

test('linear colour display conversion preserves a standard sRGB round trip', () => {
  for (const value of [0, .001, .01, .04045, .1, .5, 1]) near(linearToSrgb(srgbToLinear(value)), value, 1e-7);
  assert.equal(linearToSrgb(-1), 0);
  near(linearToSrgb(2), 1);
});
