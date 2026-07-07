# Executive Commerce Insights Dashboard

Next.js frontend for the Executive Commerce Insights application. This dashboard provides the user-facing executive chat experience, prompt shortcuts, health status, and response rendering for the Python agent backend.

## Overview

The dashboard is intentionally thin. It does not contain commerce business logic, tool selection logic, or provider configuration. It forwards user prompts to the Python FastAPI agent through a Next.js BFF layer and renders the standardized agent response contract.

LLM selection and tool routing are handled in the Python agent layer, not in this dashboard.

## Architecture

```text
Executive User
    -> Next.js Dashboard UI
    -> Next.js BFF Route (/api/chat, /api/health)
    -> Python FastAPI Agent (/chat, /health)
    -> LangGraph workflow
    -> LLM provider factory (OpenAI / Gemini / Claude)
    -> commercetools APIs
    -> normalized JSON response
    -> Dashboard response panel
```

## UI Flow

```text
Prompt card click
    -> populate textarea
    -> user edits prompt
    -> Submit
    -> dashboard checks agent health
    -> POST prompt to /api/chat
    -> BFF forwards to Python agent
    -> response rendered in chat area
```

## Features

- Executive-style single page layout
- Clickable prompt cards for common commerce questions
- Health badge for backend reachability
- Prompt validation with character limit
- Submit button and Enter-to-submit support
- Loading state while the agent responds
- Text-only assistant response rendering
- Raw error display for agent failures
- Responsive design for desktop and tablet use

## Project Structure

```text
app/
components/
lib/
tests/
docs/
```

## Environment Variables

Copy `.env.example` to `.env.local` and adjust values as needed.

```bash
NEXT_PUBLIC_APP_NAME=Executive Commerce Insight Agent
NEXT_PUBLIC_API_AGENT_BASE_URL=http://localhost:8001
NEXT_PUBLIC_ENABLE_LOGS=true
DASHBOARD_INTERACTION_SECRET=change-me
PROMPT_TEXT_CHARS_LIMIT=300
DASHBOARD_HEADER_TEXT=Executive Commerce Insights Dashboard
DASHBOARD_SUBHEADER_TEXT=AI Powered Commerce Intelligence
ENABLE_LOG=true
```

### Variable Notes

- `NEXT_PUBLIC_API_AGENT_BASE_URL`: Python agent base URL used by the BFF routes.
- `DASHBOARD_INTERACTION_SECRET`: shared secret header used for `/health` and `/chat`.
- `PROMPT_TEXT_CHARS_LIMIT`: maximum prompt length enforced in the UI and BFF.
- `NEXT_PUBLIC_ENABLE_LOGS` and `ENABLE_LOG`: control terminal logging in the dashboard layer.

## Prerequisites

- Node.js 20+
- npm 10+
- Python agent running locally at the configured backend URL

## Install

```bash
npm install
```

## Run

Start the dashboard:

```bash
npm run dev
```

The dev server runs on:

```text
http://127.0.0.1:3000
```

## Production Build

```bash
npm run build
npm run start
```

## Available Commands

- `npm run dev`: start the dashboard locally
- `npm run build`: create a production build
- `npm run start`: run the production build locally
- `npm run lint`: run ESLint
- `npm run test`: run Vitest

## How It Works

1. The user selects a prompt card or types a custom question.
2. The dashboard validates the prompt length and emptiness.
3. The dashboard checks agent health through `GET /api/health`.
4. The BFF forwards the prompt to `POST /api/chat`.
5. The Python agent selects the tool, executes commercetools calls, and asks the configured LLM to produce the response text.
6. The dashboard renders the assistant response and any raw error information.

## Backend Contract

This dashboard expects the Python agent to return the standardized contract:

```json
{
  "success": true,
  "userQuery": "Show order 100001",
  "toolUsed": "get_order_by_order_number",
  "response": "Order 100001 has been successfully retrieved.",
  "data": {},
  "error": null
}
```

The dashboard renders:
- `response` in the chat area
- `error` in a raw error block when present

The `data` field is intentionally not rendered in the UI in v1.

## Testing

The dashboard includes:
- component tests
- route tests

Run them with:

```bash
npm run test
```

## Notes

- No local storage is used.
- No database is used.
- Refresh clears the conversation.
- Provider configuration remains in the Python agent only.
- The dashboard is a BFF + presentation layer, not a commerce rules engine.

