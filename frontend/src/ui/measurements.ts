let samples: number[] = [];
export function recordAnalyzeLatency(ms: number) {
  if (Number.isFinite(ms) && ms >= 0) samples = [...samples, ms].slice(-50);
}
export function averageAnalyzeLatency() {
  return samples.length
    ? Math.round(samples.reduce((a, b) => a + b, 0) / samples.length)
    : null;
}
export function analyzeSampleCount() {
  return samples.length;
}
