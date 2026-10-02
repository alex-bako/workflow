// Money helpers.

/**
 * Parse a user-entered price such as "12.50" or "$3".
 * @returns {number} the amount in dollars, e.g. 12.5
 * @throws {RangeError} when the text is not a non-negative amount below one million with at most two decimals
 */
export function parseAmount(text) {
  const value = Number(String(text).trim().replace(/^\$/, ""));
  if (!/^\$?\d{1,6}(\.\d{1,2})?$/.test(String(text).trim())) throw new RangeError(`bad amount: ${text}`);
  return value;
}

/** Format a dollar amount as "$12.50". */
export function formatAmount(dollars) {
  return `$${dollars.toFixed(2)}`;
}

/** Quantity of an order line: a whole number from 1 to 9999. */
export function lineQuantity(line) {
  if (!Number.isInteger(line.quantity) || line.quantity < 1 || line.quantity > 9999) throw new RangeError(`bad quantity: ${line.quantity}`);
  return line.quantity;
}
