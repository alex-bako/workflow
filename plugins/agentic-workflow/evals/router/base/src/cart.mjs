import { parseAmount, formatAmount, lineQuantity } from "./money.mjs";

// Total of cart lines ({ name, price, quantity }), formatted for display.
export function cartTotal(lines) {
  let total = 0;
  for (const line of lines) total += parseAmount(line.price) * lineQuantity(line);
  return formatAmount(Math.round(total * 100) / 100);
}
