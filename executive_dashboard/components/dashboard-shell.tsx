"use client";

import { useEffect, useState, type FormEvent } from "react";

import { submitPrompt } from "@/lib/agent";
import type { AgentResponse, DashboardConfig, PromptCard } from "@/lib/types";
import { cn, formatCharacterCount } from "@/lib/utils";

type HealthState = {
  status: "healthy" | "down" | "loading";
  message: string;
};

async function readAgentHealth(): Promise<HealthState> {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const payload = (await response.json()) as { status: string; message?: string };
    if (payload.status === "healthy") {
      return { status: "healthy", message: "Agent Service Healthy" };
    }
    return { status: "down", message: payload.message ?? "Commerce Insight Agent service is currently down" };
  } catch {
    return { status: "down", message: "Commerce Insight Agent service is currently down" };
  }
}

const CARDS: PromptCard[] = [
  { label: "Order Lookup", template: "Show order details for order number <ORDER_NUMBER>" },
  { label: "Product Search", template: "Show all product details for <PRODUCT_NAME>" },
  { label: "Inventory Lookup", template: "Show inventory details for SKU <SKU>" },
  { label: "Customer Lookup", template: "Show customer details for email <EMAIL_ADDRESS>" },
  { label: "Customer Order History", template: "Show order history for email <EMAIL_ADDRESS>" },
];

export default function DashboardShell({ config }: { config: DashboardConfig }) {
  const [prompt, setPrompt] = useState("");
  const [promptCount, setPromptCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthState>({ status: "loading", message: "Checking agent service..." });
  const [latestResponse, setLatestResponse] = useState<AgentResponse | null>(null);
  const [lastSubmittedPrompt, setLastSubmittedPrompt] = useState("");
  const [localError, setLocalError] = useState<string>("");

  useEffect(() => {
    void readAgentHealth().then(setHealth);
  }, []);

  function onPromptChange(nextValue: string) {
    const nextCount = nextValue.length;
    setPrompt(nextValue);
    setPromptCount(nextCount);
    if (localError) {
      setLocalError("");
    }
  }

  function onCardClick(template: string) {
    setPrompt(template);
    setPromptCount(template.length);
    setLocalError("");
  }

  async function submitCurrentPrompt() {
    const trimmed = prompt.trim();

    if (!trimmed) {
      setLocalError("Prompt cannot be empty.");
      return;
    }
    if (trimmed.length > config.promptLimit) {
      setLocalError(`Prompt cannot exceed ${config.promptLimit} characters.`);
      return;
    }

    setLoading(true);
    setLatestResponse(null);
    setLocalError("");
    setLastSubmittedPrompt(trimmed);

    const healthState = await readAgentHealth();
    if (healthState.status !== "healthy") {
      setLoading(false);
      setLatestResponse({
        success: false,
        userQuery: trimmed,
        toolUsed: null,
        response: healthState.message,
        data: null,
        error: { code: "AGENT_DOWN", message: healthState.message },
      });
      return;
    }

    try {
      const response = await submitPrompt(trimmed);
      setLatestResponse(response);
    } catch {
      setLatestResponse({
        success: false,
        userQuery: trimmed,
        toolUsed: null,
        response: "Commerce Insight Agent service is currently down.",
        data: null,
        error: { code: "AGENT_UNAVAILABLE", message: "Commerce Insight Agent service is currently down." },
      });
    } finally {
      setLoading(false);
      void readAgentHealth().then(setHealth);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitCurrentPrompt();
  }

  const canSubmit = !loading && prompt.trim().length > 0 && prompt.trim().length <= config.promptLimit;

  return (
    <main className="min-h-screen px-4 py-5 text-[15px] text-navy sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-[1600px] flex-col gap-4">
        <header className="flex flex-col gap-3 rounded-panel border border-line bg-white/85 px-5 py-4 shadow-panel backdrop-blur sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1">
            <div className="text-2xl font-semibold tracking-tight text-navy sm:text-3xl">{config.headerText}</div>
            <div className="text-sm text-muted">{config.subheaderText}</div>
          </div>
          <div className={cn("inline-flex items-center rounded-full border px-4 py-2 text-sm font-semibold", health.status === "healthy" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700")}>
            {health.message}
          </div>
        </header>

        <section className="grid flex-1 gap-4 lg:grid-cols-[0.92fr_1.08fr]">
          <aside className="rounded-panel border border-line bg-white/80 p-4 shadow-panel">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="text-lg font-semibold">Quick Prompts</div>
                <div className="text-sm text-muted">Select a card, then fill in the details.</div>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {CARDS.map((card) => (
                <button
                  key={card.label}
                  type="button"
                  onClick={() => onCardClick(card.template)}
                  className="group rounded-panel border border-line bg-white px-4 py-4 text-left shadow-sm transition duration-200 hover:border-transparent hover:bg-citrus hover:text-white hover:shadow-lg"
                >
                  <div className="text-base font-semibold">{card.label}</div>
                  <div className="mt-2 text-sm leading-6 text-muted group-hover:text-white/90">{card.template}</div>
                </button>
              ))}
            </div>
          </aside>

          <section className="flex min-h-[70vh] flex-col rounded-panel border border-line bg-white/80 p-4 shadow-panel">
            <div className="mb-4 flex items-center justify-between border-b border-line pb-3">
              <div>
                <div className="text-lg font-semibold">Response</div>
                <div className="text-sm text-muted">Latest user query and agent reply.</div>
              </div>
              <div className="text-sm text-muted">{formatCharacterCount(promptCount, config.promptLimit)}</div>
            </div>

            <div className="flex-1 overflow-auto rounded-panel border border-line bg-[#fbfdff] p-4">
              {loading ? (
                <div className="flex h-full min-h-[260px] items-center justify-center">
                  <div className="loading-dots text-center text-lg font-semibold text-navy">
                    Loading commerce data<span><span>.</span><span>.</span><span>.</span></span>
                  </div>
                </div>
              ) : latestResponse ? (
                <div className="space-y-4">
                  <MessageBubble role="user" text={lastSubmittedPrompt} />
                  <MessageBubble role="assistant" text={latestResponse.response} />
                  {latestResponse.error ? (
                    <div className="rounded-panel border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                      <div className="mb-2 font-semibold">Raw Error</div>
                      <div className="space-y-1">
                        <div>
                          <span className="font-semibold">Code:</span> {latestResponse.error.code}
                        </div>
                        <div>
                          <span className="font-semibold">Message:</span> {latestResponse.error.message}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="flex h-full min-h-[260px] items-center justify-center text-center text-muted">
                  Submit a commerce prompt to see the agent response here.
                </div>
              )}
            </div>

            <form onSubmit={onSubmit} className="mt-4">
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <textarea
                    value={prompt}
                    onChange={(event) => onPromptChange(event.target.value.slice(0, config.promptLimit))}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        if (canSubmit) {
                          void onSubmit(event as unknown as React.FormEvent<HTMLFormElement>);
                        }
                      }
                    }}
                    rows={4}
                    placeholder="Type your commerce question here..."
                    className="w-full resize-none rounded-panel border border-line bg-white px-4 py-3 text-navy outline-none transition placeholder:text-muted focus:border-[#9cbbe8] focus:ring-2 focus:ring-[#d8e6ff]"
                  />
                  <div className="mt-2 text-left text-xs text-muted">
                    {localError ? <span className="text-red-600">{localError}</span> : formatCharacterCount(promptCount, config.promptLimit)}
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="rounded-panel border border-[#bfc9d8] bg-gradient-to-b from-[#f4f6f8] to-[#dde3eb] px-5 py-3 font-semibold text-navy shadow-sm transition hover:from-[#eef2f7] hover:to-[#d4dbe5] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Submit
                </button>
              </div>
            </form>
          </section>
        </section>
      </div>
    </main>
  );
}

function MessageBubble({ role, text }: { role: "user" | "assistant"; text: string }) {
  return (
    <div className={cn("flex", role === "user" ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[90%] rounded-panel border px-4 py-3 text-sm leading-7 shadow-sm whitespace-pre-wrap",
          role === "user" ? "border-[#c7d7ef] bg-[#eaf2ff] text-navy" : "border-[#dce6f4] bg-white text-[#103463]"
        )}
      >
        {text}
      </div>
    </div>
  );
}
