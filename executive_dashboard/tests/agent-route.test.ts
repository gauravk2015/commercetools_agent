import { describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/chat/route";
import { GET as healthGET } from "@/app/api/health/route";

describe("dashboard routes", () => {
  it("returns validation errors for empty prompts", async () => {
    const response = await POST(new Request("http://localhost/api/chat", { method: "POST", body: JSON.stringify({ prompt: "   " }) }));
    const payload = await response.json();
    expect(response.status).toBe(400);
    expect(payload.success).toBe(false);
    expect(payload.error.code).toBe("INVALID_PROMPT");
  });

  it("returns down status when the backend is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("down", { status: 503 })));
    const response = await healthGET();
    const payload = await response.json();
    expect(payload.status).toBe("down");
  });
});
