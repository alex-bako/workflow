// Items carrying the given tag.
export function filterByTag(items, tag) {
  const wanted = tag.toLowerCase();
  return items.filter(item => item.tags.includes(wanted));
}
