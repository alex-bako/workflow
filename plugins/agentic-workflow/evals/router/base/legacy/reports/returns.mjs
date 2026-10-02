// Retired returns report (replaced by the analytics service). Kept for reference.

export function group4(rows) {
  const groups = new Map();
  for (const row of rows) {
    const key = row.reason ?? "unknown";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  return groups;
}

export function totals4(rows) {
  const out = [];
  for (const [key, members] of group4(rows)) {
    let count = 0;
    let weight = 0;
    for (const member of members) {
      count += 1;
      weight += member.weight ?? 0;
    }
    out.push({ key, count, weight, average: count ? weight / count : 0 });
  }
  return out.sort((a, b) => b.count - a.count || String(a.key).localeCompare(String(b.key)));
}

export function render4(rows) {
  const header = "RETURNS REPORT";
  const body = totals4(rows).map(row => `${row.key}\t${row.count}\t${row.weight}\t${row.average.toFixed(1)}`);
  return [header, "=".repeat(header.length), ...body].join("\n");
}
