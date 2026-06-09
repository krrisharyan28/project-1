/** Shared formatting + risk helpers used across the app. */

export function formatCurrency(amount, currency = "USD") {
  const value = Number(amount);
  if (Number.isNaN(value)) return `${amount}`;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const RISK_LEVELS = ["low", "medium", "high"];

/** Tailwind classes for a risk-level badge. */
export function riskBadgeClasses(level) {
  switch (level) {
    case "high":
      return "bg-red-100 text-red-700 ring-red-600/20";
    case "medium":
      return "bg-amber-100 text-amber-700 ring-amber-600/20";
    default:
      return "bg-green-100 text-green-700 ring-green-600/20";
  }
}

/** Hex colors (match tailwind.config risk palette) for charts. */
export const RISK_COLORS = {
  low: "#16a34a",
  medium: "#d97706",
  high: "#dc2626",
};

export const ALERT_STATUS_LABELS = {
  open: "Open",
  confirmed_fraud: "Confirmed fraud",
  dismissed: "Dismissed",
};
