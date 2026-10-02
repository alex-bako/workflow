// @generated from the order schema of the API repository. Do not edit.
// digest: 5f0c2a91d4

export const orderLineSchema = {
  type: "object",
  properties: {
    id: {
      type: "string",
      description: "Order id",
    },
    customer: {
      type: "string",
      description: "Customer id",
    },
    price: {
      type: "string",
      description: "Unit price, dollar text such as 12.50",
    },
    quantity: {
      type: "integer",
      description: "Units ordered",
    },
    currency: {
      type: "string",
      description: "ISO 4217 code",
    },
    createdAt: {
      type: "string",
      description: "ISO 8601 timestamp",
    },
    note: {
      type: "string",
      description: "Free-text note",
    },
  },
  required: ["id", "customer", "price", "quantity"],
};
