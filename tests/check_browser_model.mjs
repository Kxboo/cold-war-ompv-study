// JSON bridge used by Python's independent CPU/reference parity check.
import { gather, combine, composite } from '../site/ompv-model.mjs';
let data = '';
for await (const chunk of process.stdin) data += chunk;
const result = JSON.parse(data).map(testCase => {
  const samples = gather(testCase.ids, testCase.uv, testCase.controls);
  const contributions = combine(samples);
  return { samples: samples.map(sample => [sample.material, sample.weight, sample.control]),
    contributions: contributions.map(({ material, coverage, weighted_control, mean_control }) => ({ material, coverage, weighted_control, mean_control })),
    colour: composite(contributions, testCase.colours, testCase.reveal) };
});
process.stdout.write(JSON.stringify(result));
