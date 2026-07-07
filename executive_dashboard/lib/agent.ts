import type { AgentResponse } from "@/lib/types";

export async function submitPrompt(prompt: string): Promise<AgentResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  return (await response.json()) as AgentResponse;
}
