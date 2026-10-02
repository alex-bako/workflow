// Durations as whole seconds: "1h30m" <-> 5400.
const UNITS = { d: 86400, h: 3600, m: 60, s: 1 };
const SHAPE = /^(\d+(?:\.\d+)?[dhms])+$/;

export function parseDuration(text) {
  if (!SHAPE.test(text)) throw new RangeError(`bad duration: ${text}`);
  const seen = new Set();
  let seconds = 0;
  for (const [, n, unit] of text.matchAll(/(\d+(?:\.\d+)?)([dhms])/g)) {
    if (seen.has(unit)) throw new RangeError(`repeated unit: ${unit}`);
    seen.add(unit);
    seconds += Number.parseFloat(n) * UNITS[unit];
  }
  return seconds;
}

export function formatDuration(seconds) {
  if (seconds === 0) return "0s";
  const parts = [];
  let rest = seconds;
  for (const [unit, size] of Object.entries(UNITS)) {
    const n = Math.floor(rest / size);
    rest -= n * size;
    if (n > 0) parts.push(`${n}${unit}`);
  }
  return parts.join("");
}
