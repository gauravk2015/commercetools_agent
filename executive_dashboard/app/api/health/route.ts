import { NextResponse } from "next/server";

import { getServerConfig } from "@/lib/env";
import { logEvent } from "@/lib/logger";

export async function GET() {
  const config = getServerConfig();

  try {
    const response = await fetch(`${config.agentBaseUrl}/health`, {
      method: "GET",
      headers: {
        "x-dashboard-secret": config.dashboardSecret,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      logEvent(config.enableLogs, "health_down", { status: response.status });
      return NextResponse.json(
        {
          status: "down",
          message: "Commerce Insight Agent service is currently down",
        },
        { status: 503 }
      );
    }

    const payload = await response.json().catch(() => ({ status: "healthy" }));
    if (payload?.status !== "healthy") {
      logEvent(config.enableLogs, "health_down", payload);
      return NextResponse.json(
        {
          status: "down",
          message: "Commerce Insight Agent service is currently down",
        },
        { status: 503 }
      );
    }

    logEvent(config.enableLogs, "health_ok", payload);
    return NextResponse.json({ status: "healthy" });
  } catch (error) {
    logEvent(config.enableLogs, "health_error", error);
    return NextResponse.json(
      {
        status: "down",
        message: "Commerce Insight Agent service is currently down",
      },
      { status: 503 }
    );
  }
}
