import { parseAmount, lineQuantity } from "./money.mjs";

// Header printed above every invoice.
export function invoiceHeader(number, date) {
  return `Invoice ${number} — ${date}`;
}

// One printed invoice line, e.g. "Tea x2 @ $3.50 = $7.00".
export function invoiceLine(line) {
  const unit = parseAmount(line.price);
  const sum = unit * lineQuantity(line);
  return `${line.name} x${line.quantity} @ $${unit.toFixed(2)} = $${sum.toFixed(2)}`;
}
