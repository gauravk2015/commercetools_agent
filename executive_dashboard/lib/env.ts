import type { DashboardConfig, ServerConfig } from "@/lib/types";

function toNumber(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toBoolean(value: string | undefined, fallback = false): boolean {
  if (value === undefined) return fallback;
  return value.toLowerCase() === "true";
}

export function getDashboardConfig(): DashboardConfig {
  return {
    appName: process.env.NEXT_PUBLIC_APP_NAME ?? "Executive Commerce Insight Agent",
    headerText: process.env.DASHBOARD_HEADER_TEXT ?? "Executive Commerce Insights Dashboard",
    subheaderText: process.env.DASHBOARD_SUBHEADER_TEXT ?? "AI Powered Commerce Intelligence",
    promptLimit: toNumber(process.env.PROMPT_TEXT_CHARS_LIMIT, 300),
    enableLogs: toBoolean(process.env.NEXT_PUBLIC_ENABLE_LOGS, true) || toBoolean(process.env.ENABLE_LOG, true),
  };
}

export function getServerConfig(): ServerConfig {
  return {
    agentBaseUrl: process.env.NEXT_PUBLIC_API_AGENT_BASE_URL ?? "http://localhost:8001",
    dashboardSecret: process.env.DASHBOARD_INTERACTION_SECRET ?? "",
    promptLimit: toNumber(process.env.PROMPT_TEXT_CHARS_LIMIT, 300),
    enableLogs: toBoolean(process.env.NEXT_PUBLIC_ENABLE_LOGS, true) || toBoolean(process.env.ENABLE_LOG, true),
  };
}
