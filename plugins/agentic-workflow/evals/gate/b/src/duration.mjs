// Durations as whole seconds: "1h30m" <-> 5400.
const UNITS = [["d", 86400], ["h", 3600], ["m", 60], ["s", 1]];
const PATTERN = /^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/;

export function parseDuration(text) {
  const match = PATTERN.exec(text);
  if (!text || !match) throw new RangeError(`bad duration: ${text}`);
  let seconds = 0;
  UNITS.forEach(([, size], i) => {
    if (match[i + 1] !== undefined) seconds += Number.parseInt(match[i + 1], 10) * size;
  });
  return seconds;
}

export function formatDuration(seconds) {
  const parts = [];
  let rest = seconds;
  for (const [unit, size] of UNITS) {
    const n = Math.floor(rest / size);
    rest -= n * size;
    if (n > 0) parts.push(`${n}${unit}`);
  }
  return parts.join("");
}
