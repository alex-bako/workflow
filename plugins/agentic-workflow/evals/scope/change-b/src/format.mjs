// One list row: "[x] Title <url>" for read items, "[ ] Title <url>" otherwise.
export function formatItem({ title, url, read }) {
  const row = `[${read ? "x" : " "}] ${title}`;
  return url ? `${row} <${url}>` : row;
}
