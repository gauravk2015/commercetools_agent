export type PromptCard = {
  label: string;
  template: string;
};

export type AgentResponse = {
  success: boolean;
  userQuery: string;
  toolUsed: string | null;
  response: string;
  data: Record<string, unknown> | unknown[] | null;
  error: { code: string; message: string } | null;
};

export type DashboardConfig = {
  appName: string;
  headerText: string;
  subheaderText: string;
  promptLimit: number;
  enableLogs: boolean;
};

export type ServerConfig = {
  agentBaseUrl: string;
  dashboardSecret: string;
  promptLimit: number;
  enableLogs: boolean;
};
