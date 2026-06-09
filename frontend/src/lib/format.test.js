import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatDateTime,
  riskBadgeClasses,
  RISK_COLORS,
  ALERT_STATUS_LABELS,
} from "./format";

describe("formatCurrency", () => {
  it("formats USD amounts", () => {
    expect(formatCurrency(1234.5, "USD")).toBe("$1,234.50");
  });

  it("handles string input", () => {
    expect(formatCurrency("42", "USD")).toBe("$42.00");
  });

  it("falls back gracefully on non-numeric input", () => {
    expect(formatCurrency("abc")).toBe("abc");
  });
});

describe("formatDateTime", () => {
  it("returns a dash for empty input", () => {
    expect(formatDateTime(null)).toBe("—");
  });

  it("formats an ISO timestamp to a readable string", () => {
    const out = formatDateTime("2026-05-10T11:00:00Z");
    expect(out).toMatch(/2026/);
  });
});

describe("riskBadgeClasses", () => {
  it("returns red classes for high risk", () => {
    expect(riskBadgeClasses("high")).toContain("red");
  });
  it("returns amber classes for medium risk", () => {
    expect(riskBadgeClasses("medium")).toContain("amber");
  });
  it("defaults to green for low/unknown", () => {
    expect(riskBadgeClasses("low")).toContain("green");
    expect(riskBadgeClasses("anything")).toContain("green");
  });
});

describe("constants", () => {
  it("exposes a color per risk level", () => {
    expect(RISK_COLORS).toHaveProperty("low");
    expect(RISK_COLORS).toHaveProperty("medium");
    expect(RISK_COLORS).toHaveProperty("high");
  });
  it("maps alert statuses to labels", () => {
    expect(ALERT_STATUS_LABELS.confirmed_fraud).toBe("Confirmed fraud");
  });
});
