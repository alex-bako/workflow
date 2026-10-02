// Discount rules. Not wired into the cart yet.

// A rule is { code, percent }; codes are case-insensitive.
export function findRule(rules, code) {
  const wanted = code.trim().toUpperCase();
  return rules.find(rule => rule.code.toUpperCase() === wanted) ?? null;
}

export function isValidPercent(percent) {
  return Number.isInteger(percent) && percent > 0 && percent <= 90;
}
