// Parse one reading-list line: "<title words> <url>".
export function parseItem(line) {
  const words = line.trim().split(/\s+/);
  const url = words.find(word => /^https?:\/\//.test(word)) ?? null;
  const title = words.filter(word => word !== url).join(" ");
  return { title, url, read: false };
}
