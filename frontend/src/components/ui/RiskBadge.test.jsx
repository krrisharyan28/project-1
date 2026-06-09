import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import RiskBadge from "./RiskBadge";

describe("RiskBadge", () => {
  it("renders the risk level text", () => {
    render(<RiskBadge level="high" />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("applies the color matching the level", () => {
    render(<RiskBadge level="medium" />);
    expect(screen.getByText("medium").className).toContain("amber");
  });
});
