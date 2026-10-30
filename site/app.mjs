import { CORNERS, clamp, gather, combine, traceComposite, materialColour, toCss } from './ompv-model.mjs';

const $ = selector => document.querySelector(selector);
const fullCorners = ['top-left', 'top-right', 'bottom-left', 'bottom-right'];
const number = (value, digits = 4) => value.toFixed(digits);
const rgb = colour => colour.map(value => number(value, 3)).join(', ');
const presets = {
  duplicates: { ids: [7, 7, 2, 7], uv: [.375, .625], controls: [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]], reveal: .5 },
  four: { ids: [12, 3, 255, 7], uv: [.5, .5], controls: [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]], reveal: .88 },
  controls: { ids: [7, 7, 2, 7], uv: [.375, .625], controls: [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]], reveal: .5 },
  edge: { ids: [0, 255, 255, 255], uv: [.94, .08], controls: [[1, 1, 1], [1, .6, .3], [.35, .65, 1], [1, 1, 1]], reveal: .65 },
};
let state;
let selectedCorner = 0;
let layerKey = '';
let liveTimer;
let lastTrace;

function ensureMaterial(id, reveal = .5) {
  state.materials[id] ??= { colour: materialColour(id), reveal, width: 128 / 255, exponent: 128 / 255 };
}

function setPreset(name) {
  const preset = presets[name];
  state = { ids: [...preset.ids], uv: [...preset.uv], controls: preset.controls.map(control => [...control]),
    materials: {}, mode: state?.mode ?? 'teaching' };
  state.ids.forEach(id => ensureMaterial(id, preset.reveal));
  selectedCorner = 0;
  document.querySelectorAll('[data-preset]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.preset === name)));
  layerKey = '';
  update();
  announce();
}

function markCustom() {
  document.querySelectorAll('[data-preset]').forEach(button => button.setAttribute('aria-pressed', 'false'));
}

function createControls() {
  $('#corner-editors').innerHTML = CORNERS.map((corner, index) => `
    <div class="corner-editor" id="corner-${index}">
      <label for="id-${index}">${corner} / MATERIAL ID</label>
      <input id="id-${index}" type="number" min="0" max="255" step="1" inputmode="numeric" aria-label="${fullCorners[index]} material ID, 0 to 255">
      <button class="edit-tint" type="button" data-corner="${index}" aria-label="Edit ${fullCorners[index]} RGB control" aria-pressed="false"></button>
      <span class="corner-tint" id="corner-tint-${index}"></span>
    </div>`).join('');
  $('#tint-sliders').innerHTML = ['R', 'G', 'B'].map((channel, index) => `
    <label class="compact-slider" for="tint-${index}"><span>${channel}</span>
      <input id="tint-${index}" type="range" min="0" max="1" step="0.01" aria-label="${fullCorners[0]} ${channel} control">
      <output id="tint-value-${index}" for="tint-${index}"></output>
    </label>`).join('');
  $('#sample-cells').innerHTML = CORNERS.map((corner, index) => `<div class="sample-cell" id="sample-cell-${index}"><span></span></div>`).join('');
  $('#sample-centres').innerHTML = [[100, 100], [300, 100], [100, 300], [300, 300]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="4"/>`).join('');
  CORNERS.forEach((corner, index) => {
    const input = $(`#id-${index}`);
    input.addEventListener('input', () => {
      if (input.value === '' || !input.validity.valid) return;
      state.ids[index] = Number(input.value);
      ensureMaterial(state.ids[index]);
      markCustom();
      update();
    });
    input.addEventListener('change', () => {
      if (input.value === '' || !input.validity.valid) {
        input.value = state.ids[index];
        $('#explorer-status').textContent = 'Material IDs must be whole numbers from 0 to 255. The previous valid value has been restored.';
      } else announce();
    });
    $(`[data-corner="${index}"]`).addEventListener('click', () => {
      selectedCorner = index;
      update();
    });
  });
  ['R', 'G', 'B'].forEach((channel, index) => {
    $(`#tint-${index}`).addEventListener('input', event => {
      state.controls[selectedCorner][index] = Number(event.target.value);
      markCustom();
      update();
    });
    $(`#tint-${index}`).addEventListener('change', announce);
  });
  ['u', 'v'].forEach((axis, index) => {
    $(`#${axis}`).addEventListener('input', event => {
      state.uv[index] = Number(event.target.value);
      markCustom();
      update();
    });
    $(`#${axis}`).addEventListener('change', announce);
  });
  document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => setPreset(button.dataset.preset)));
  $('#reset').addEventListener('click', () => { state.mode = 'teaching'; setPreset('duplicates'); });
  $('#reveal-mode').addEventListener('change', event => { state.mode = event.target.value; update(); announce(); });
  const board = $('#sample-board');
  function setPosition(event) {
    const bounds = board.getBoundingClientRect();
    state.uv = [clamp((event.clientX - bounds.left) / bounds.width), clamp((event.clientY - bounds.top) / bounds.height)]
      .map(value => Math.round(value * 1000) / 1000);
    markCustom();
    update();
  }
  board.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    board.setPointerCapture(event.pointerId);
    setPosition(event);
  });
  board.addEventListener('pointermove', event => { if (board.hasPointerCapture(event.pointerId)) setPosition(event); });
  board.addEventListener('pointerup', event => {
    if (board.hasPointerCapture(event.pointerId)) board.releasePointerCapture(event.pointerId);
    announce();
  });
}

function buildLayers(trace) {
  const key = `${state.mode}:${trace.layers.map(layer => layer.material).join(',')}`;
  if (key === layerKey) return;
  layerKey = key;
  $('#layer-stack').innerHTML = trace.layers.map(layer => {
    const id = layer.material;
    return `<div class="layer-card" id="layer-${id}">
      <div class="layer-card-heading"><i class="id-dot" style="--dot-colour:${toCss(state.materials[id].colour)}"></i><strong>ID ${id}</strong><small>${layer.primary ? 'OPAQUE BASE' : 'OVERLAY'}</small></div>
      <div class="layer-coverage"><span>Coverage</span><b id="coverage-${id}"></b></div>
      <div class="coverage-track" style="--layer-colour:${toCss(state.materials[id].colour)}"><span id="coverage-bar-${id}"></span></div>
      <div class="layer-bottom"><span>α <b id="alpha-${id}"></b></span><span>Final <b id="final-${id}"></b></span></div>
      ${layer.primary ? '' : `<div class="layer-reveal"><label for="reveal-${id}"><span>${state.mode === 'observed' ? 'Sample' : 'Reveal'}</span><input id="reveal-${id}" type="range" min="0" max="1" step="0.01" aria-label="Material ${id} reveal ${state.mode === 'observed' ? 'sample' : 'value'}"><output id="reveal-value-${id}"></output></label>
      ${state.mode === 'observed' ? `<div class="advanced-reveal">${['width', 'exponent'].map(parameter => `<label for="${parameter}-${id}"><span>${parameter === 'width' ? 'Width' : 'Exp.'}</span><input id="${parameter}-${id}" type="range" min="0" max="255" step="1" aria-label="Material ${id} reveal ${parameter} byte"><output id="${parameter}-value-${id}"></output></label>`).join('')}</div><p class="reveal-bounds" id="bounds-${id}"></p>` : ''}</div>`}
    </div>`;
  }).join('');
  for (const layer of trace.layers) {
    if (layer.primary) continue;
    const id = layer.material;
    const parameters = state.mode === 'observed' ? ['reveal', 'width', 'exponent'] : ['reveal'];
    for (const parameter of parameters) {
      $(`#${parameter}-${id}`).addEventListener('input', event => {
        state.materials[id][parameter] = Number(event.target.value) / (parameter === 'reveal' ? 1 : 255);
        markCustom();
        update();
      });
      $(`#${parameter}-${id}`).addEventListener('change', announce);
    }
  }
}

function update() {
  const indexMap = [state.ids.slice(0, 2), state.ids.slice(2)];
  const controls = [state.controls.slice(0, 2), state.controls.slice(2)];
  const samples = gather(indexMap, state.uv, controls);
  const entries = combine(samples);
  const trace = traceComposite(entries, state.materials, state.mode);
  lastTrace = trace;
  state.ids.forEach((id, index) => {
    const input = $(`#id-${index}`);
    if (document.activeElement !== input) input.value = id;
    $(`#corner-${index}`).classList.toggle('is-selected', selectedCorner === index);
    $(`[data-corner="${index}"]`).setAttribute('aria-pressed', String(selectedCorner === index));
    $(`[data-corner="${index}"]`).style.background = toCss(state.controls[index]);
    $(`#corner-tint-${index}`).textContent = state.controls[index].map(value => number(value, 2)).join(' / ');
    $(`#sample-cell-${index}`).style.setProperty('--cell-colour', toCss(state.materials[id].colour));
    $(`#sample-cell-${index} span`).textContent = `${CORNERS[index]} · ID ${String(id).padStart(3, '0')}`;
  });
  $('#selected-corner-label').textContent = `/ ${fullCorners[selectedCorner]}`;
  ['R', 'G', 'B'].forEach((channel, index) => {
    $(`#tint-${index}`).value = state.controls[selectedCorner][index];
    $(`#tint-value-${index}`).textContent = number(state.controls[selectedCorner][index], 2);
    $(`#tint-${index}`).setAttribute('aria-label', `${fullCorners[selectedCorner]} ${channel} control`);
  });
  ['u', 'v'].forEach((axis, index) => { $(`#${axis}`).value = state.uv[index]; $(`#${axis}-value`).textContent = number(state.uv[index], 3); });
  const [px, py] = state.uv.map(value => value * 400);
  $('#sample-cursor').setAttribute('transform', `translate(${px}, ${py})`);
  $('#sample-connections').setAttribute('d', samples.filter(sample => sample.weight > 0).map(sample => `M${px} ${py}L${sample.texel[0] * 200 + 100} ${sample.texel[1] * 200 + 100}`).join(''));
  const position = state.uv.map(value => value * 2 - .5);
  const fraction = position.map(value => value - Math.floor(value));
  $('#coordinate-note').textContent = `p = (${position.map(value => number(value, 3)).join(', ')}) · f = (${fraction.map(value => number(value, 3)).join(', ')})`;
  $('#gather-rows').innerHTML = samples.map(sample => `<tr${sample.weight === 0 ? ' class="is-zero"' : ''}><td>${sample.corner}</td><td>(${sample.texel.join(', ')})</td><td><i class="id-dot" style="--dot-colour:${toCss(state.materials[sample.material].colour)}"></i>${sample.material}</td><td>${number(sample.weight)}</td></tr>`).join('');
  buildLayers(trace);
  for (const layer of trace.layers) {
    const id = layer.material;
    $(`#coverage-${id}`).textContent = number(layer.coverage);
    $(`#coverage-bar-${id}`).style.width = `${layer.coverage * 100}%`;
    $(`#alpha-${id}`).textContent = number(layer.alpha, 3);
    $(`#final-${id}`).textContent = number(layer.finalWeight, 3);
    if (!layer.primary) {
      $(`#reveal-${id}`).value = state.materials[id].reveal;
      $(`#reveal-value-${id}`).textContent = number(state.materials[id].reveal, 2);
      if (state.mode === 'observed') {
        for (const parameter of ['width', 'exponent']) {
          const byte = Math.round(state.materials[id][parameter] * 255);
          $(`#${parameter}-${id}`).value = byte;
          $(`#${parameter}-value-${id}`).textContent = byte;
        }
        $(`#bounds-${id}`).textContent = `2A→${number(layer.reveal.coverage, 3)} · interval [${number(layer.reveal.low, 3)}, ${number(layer.reveal.high, 3)}]`;
      }
    }
  }
  $('#output-swatch').style.background = toCss(trace.colour);
  $('#output-swatch').setAttribute('aria-label', `Synthetic composed colour, linear RGB ${rgb(trace.colour)}`);
  $('#output-rgb').textContent = rgb(trace.colour);
  $('#unique-count').textContent = entries.length;
  $('#evaluation-count').textContent = entries.length;
  $('#coverage-sum').textContent = number(entries.reduce((sum, entry) => sum + entry.coverage, 0));
  $('#reveal-mode').value = state.mode;
  const observed = state.mode === 'observed';
  $('#mode-scope').textContent = observed
    ? 'Only the reveal equation is replaced. Selection still uses the teaching model, which omits zero-weight IDs. Width and exponent are bytes ÷ 255; the sample is synthetic.'
    : 'An illustrative rule inspired by the public presentation. Not the recovered Cold War shader.';
  $('#equation-title').textContent = observed ? 'Observed reveal equation' : 'Teaching reveal rule';
  $('#equation-code').textContent = observed
    ? 'a = clamp(2 × coverage)\nc = clamp(0.998a + 0.001); inv = 1−c\nlo = clamp(inv − width × c^exp)\nhi = clamp(inv + width × inv^exp)\nraw = clamp((sample−lo) / (hi−lo))\nα = max(raw, clamp((a−0.99) × 100))'
    : 'α = clamp(2 × coverage − 1 + reveal)\nresult = (1−α) × previous + α × layer';
  $('#equation-note').textContent = observed
    ? 'This uses the reveal-enabled equation with teaching selection. The captured variant can keep a zero-weight lowest ID as its base; this example omits such IDs. If the interval collapses, 0/0 becomes 0 and infinities clamp, then the endpoint term applies.'
    : 'The first participating layer is opaque. Later layers can occlude earlier ones, so final weights differ from bilinear coverage.';
  $('#trace-data').innerHTML = `<table><caption>Current intermediate values · ordered by numeric material ID</caption><thead><tr><th>ID</th><th>Coverage A</th><th>Weighted control C</th><th>Mean control C/A</th><th>α</th><th>Final weight</th></tr></thead><tbody>${trace.layers.map(layer => `<tr><td>${layer.material}</td><td>${number(layer.coverage)}</td><td>(${rgb(layer.weighted_control)})</td><td>(${rgb(layer.mean_control)})</td><td>${number(layer.alpha)}</td><td>${number(layer.finalWeight)}</td></tr>`).join('')}</tbody></table>`;
}

function announce() {
  clearTimeout(liveTimer);
  liveTimer = setTimeout(() => {
    const ids = lastTrace.layers.map(layer => layer.material).join(', ');
    $('#explorer-status').textContent = `${lastTrace.layers.length} participating layers in order: ${ids}. Total coverage 1. Composed linear RGB: ${rgb(lastTrace.colour)}. ${state.mode === 'teaching' ? 'Teaching reveal rule.' : 'Observed reveal equation with teaching selection.'}`;
  }, 150);
}

createControls();
setPreset('duplicates');
