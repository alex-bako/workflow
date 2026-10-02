// Retired monthly report (replaced by the analytics service). Kept for reference.

export function group0(rows) {
  const groups = new Map();
  for (const row of rows) {
    const key = row.month ?? "unknown";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  return groups;
}

export function totals0(rows) {
  const out = [];
  for (const [key, members] of group0(rows)) {
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

export function render0(rows) {
  const header = "MONTHLY REPORT";
  const body = totals0(rows).map(row => `${row.key}\t${row.count}\t${row.weight}\t${row.average.toFixed(1)}`);
  return [header, "=".repeat(header.length), ...body].join("\n");
}
