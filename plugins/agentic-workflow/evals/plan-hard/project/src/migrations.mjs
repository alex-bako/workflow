// steps[n] upgrades a saved list from version n to version n + 1.
const steps = {
  1: data => ({
    version: 2,
    items: data.items.map(({ title, url, done }) => ({ title, url, read: Boolean(done) })),
  }),
};

export function migrate(data, target) {
  let current = data;
  while (current.version < target) {
    const step = steps[current.version];
    if (!step) throw new RangeError(`no migration from version ${current.version}`);
    current = step(current);
  }
  return current;
}
