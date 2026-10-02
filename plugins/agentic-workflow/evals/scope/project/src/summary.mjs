// Summary line shown under the list.
export function summary(items) {
  const unread = items.filter(item => !item.read).length;
  return `${items.length} items, ${unread} unread`;
}
