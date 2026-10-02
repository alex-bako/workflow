const TAG = /^#(\w+)$/;

// Parse one reading-list line: "<title words> <url> #tag ...".
export function parseItem(line) {
  const words = line.trim().split(/\s+/);
  const url = words.find(word => /^https?:\/\//.test(word)) ?? null;
  const tags = [];
  for (const word of words) {
    const match = TAG.exec(word);
    const tag = match?.[1].toLowerCase();
    if (tag && !tags.includes(tag)) tags.push(tag);
  }
  const title = words.filter(word => word !== url && !TAG.test(word)).join(" ");
  return { title, url, read: false, tags };
}
