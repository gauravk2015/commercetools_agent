import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DashboardShell from "@/components/dashboard-shell";

describe("DashboardShell", () => {
  it("renders header and submit button", () => {
    render(
      <DashboardShell
        config={{
          appName: "Executive Commerce Insight Agent",
          headerText: "Executive Commerce Insights Dashboard",
          subheaderText: "AI Powered Commerce Intelligence",
          promptLimit: 300,
          enableLogs: false,
        }}
      />
    );

    expect(screen.getByText("Executive Commerce Insights Dashboard")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
    expect(screen.queryByText("Commerce Data")).not.toBeInTheDocument();
  });
});
