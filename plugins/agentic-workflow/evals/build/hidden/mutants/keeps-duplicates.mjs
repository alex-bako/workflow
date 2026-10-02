// Parse one reading-list line: "<title words> <url>", with optional "#tag" tokens.
export function parseItem(line) {
  const words = line.trim().split(/\s+/);
  const url = words.find(word => /^https?:\/\//.test(word)) ?? null;
  const isTag = word => /^#\w+$/.test(word);
  const tags = words.filter(isTag).map(word => word.slice(1).toLowerCase());
  const title = words.filter(word => word !== url && !isTag(word)).join(" ");
  return { title, url, read: false, tags };
}
