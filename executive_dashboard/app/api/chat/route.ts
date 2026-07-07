import { NextResponse } from "next/server";

import { getServerConfig } from "@/lib/env";
import { logEvent } from "@/lib/logger";

type AgentResponse = {
  success: boolean;
  userQuery: string;
  toolUsed: string | null;
  response: string;
  data: Record<string, unknown> | unknown[] | null;
  error: { code: string; message: string } | null;
};

function buildErrorResponse(userQuery: string, message: string, code: string, toolUsed: string | null = null): AgentResponse {
  return {
    success: false,
    userQuery,
    toolUsed,
    response: message,
    data: null,
    error: { code, message },
  };
}

export async function POST(request: Request) {
  const config = getServerConfig();

  try {
    const body = (await request.json()) as { prompt?: unknown };
    const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";

    if (!prompt) {
      return NextResponse.json(buildErrorResponse("", "Prompt cannot be empty.", "INVALID_PROMPT"), { status: 400 });
    }

    if (prompt.length > config.promptLimit) {
      return NextResponse.json(
        buildErrorResponse("", `Prompt cannot exceed ${config.promptLimit} characters.`, "PROMPT_TOO_LONG"),
        { status: 400 }
      );
    }

    const response = await fetch(`${config.agentBaseUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-dashboard-secret": config.dashboardSecret,
      },
      body: JSON.stringify({ prompt }),
      cache: "no-store",
    });

    const payload = (await response.json()) as AgentResponse;
    logEvent(config.enableLogs, "chat_forward", { prompt, status: response.status, toolUsed: payload.toolUsed });
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    logEvent(config.enableLogs, "chat_error", error);
    return NextResponse.json(
      buildErrorResponse("", "Commerce Insight Agent service is currently down.", "AGENT_UNAVAILABLE"),
      { status: 503 }
    );
  }
}
