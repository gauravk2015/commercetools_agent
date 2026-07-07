# Executive Agent

Python FastAPI backend for the Executive Commerce Insights platform.

This service receives a single natural-language `prompt` from the dashboard, selects the appropriate commerce tool, calls commercetools through the official REST APIs, normalizes the payload, and uses the configured LLM provider to produce the final business response.

The dashboard never talks to commercetools directly. The LLM provider choice is also handled here at the agent layer, not in the frontend.

## What It Does

- Receives dashboard requests over HTTP as JSON
- Validates the shared dashboard secret header
- Selects the right tool through a LangGraph workflow
- Calls commercetools with an authenticated bearer token
- Normalizes raw commerce payloads into business-friendly JSON
- Generates a human-readable response with the configured LLM provider
- Returns a standardized response contract to the dashboard

## Architecture

```text
Dashboard
  -> POST /chat
  -> FastAPI agent
  -> LangGraph tool selection
  -> CommerceToolsClient
  -> commercetools REST APIs
  -> normalized JSON
  -> LLM provider factory
  -> human-readable response
  -> dashboard
```

## Supported Business Tools

- Order lookup by order number
- Product search by name
- Inventory lookup by SKU
- Customer lookup by email
- Customer order history by email

## Prerequisites

- Use Python 3.10+ through your preferred environment manager such as venv, conda, pyenv, or VS Code.
- Valid commercetools credentials
- A configured LLM API key and endpoint

## Environment

Copy `.env.example` to `.env` and provide the required values.

### Core settings

```bash
APP_NAME=Executive Commerce Insights Agent
APP_ENV=local
ENABLE_LOGS=true
DASHBOARD_INTERACTION_SECRET=change-me
ACTIVE_PROVIDER=openai
```

### commercetools settings

```bash
CTP_PROJECT_KEY=
CTP_CLIENT_ID=
CTP_CLIENT_SECRET=
CTP_AUTH_URL=
CTP_API_URL=
CTP_SCOPES=
```

### LLM configuration

LLM endpoints are environment-driven through the agent layer:

```bash
LLM_SYSTEM_PROMPT=You are an AI Commerce Operations Agent that assists customer support and commerce operations teams...
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_ENDPOINT=https://api.openai.com/v1/chat/completions
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
CLAUDE_API_KEY=
CLAUDE_MODEL=claude-sonnet-5
CLAUDE_API_ENDPOINT=https://api.anthropic.com/v1/messages
```

The frontend does not configure providers. The active provider is selected in this backend through `ACTIVE_PROVIDER`.

## Installation and Running the Application

The Python Agent requires **Python 3.10 or later** and `pip` for installing project dependencies.

### Prerequisites

Verify that Python and `pip` are available:

```bash
python3 --version
python3 -m pip --version
```

> **Note:** On some systems, the Python command is `python` instead of `python3`. Use the command that points to Python 3.10 or later.

### Navigate to the Python Agent Directory

```bash
cd executive_agent
```

Choose one of the setup options below.

---

### Option 1: Setup with a Virtual Environment (Recommended)

A virtual environment creates an isolated Python environment for the project and prevents project dependencies from affecting your system Python installation.

#### Create the Virtual Environment

```bash
python3 -m venv .venv
```

#### Activate the Virtual Environment

##### Linux, macOS, or WSL

```bash
source .venv/bin/activate
```

##### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

##### Windows Command Prompt

```cmd
.venv\Scripts\activate.bat
```

After activation, your terminal should display `(.venv)` before the command prompt.

#### Upgrade pip

```bash
python -m pip install --upgrade pip
```

#### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

#### Configure Environment Variables

Create the `.env` file and configure the required environment variables as described in the **Environment Configuration** section of this README.

#### Start the Application

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### Deactivate the Virtual Environment

To leave the virtual environment:

```bash
deactivate
```

#### Ubuntu/Debian Troubleshooting

If creating the virtual environment fails with an `ensurepip is not available` error, install Python virtual environment support:

```bash
sudo apt update
sudo apt install python3-venv
```

Then create the virtual environment again:

```bash
python3 -m venv .venv
```

---

### Option 2: Setup with System Python

Use this option to install the project dependencies into your currently active Python environment.

#### Install Dependencies

```bash
python3 -m pip install -r requirements.txt
```

#### Configure Environment Variables

Create the `.env` file and configure the required environment variables as described in the **Environment Configuration** section of this README.

#### Start the Application

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

### Option 3: Setup with Conda, pyenv, VS Code, or Another Python Environment Manager

Create or select a Python 3.10+ environment using your preferred environment management tool.

#### Verify the Active Python Environment

```bash
python --version
python -m pip --version
```

#### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

#### Configure Environment Variables

Create the `.env` file and configure the required environment variables as described in the **Environment Configuration** section of this README.

#### Start the Application

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

### Verify the Application

After starting the application, open the FastAPI Swagger UI in your browser:

```text
http://localhost:8001/docs
```

If the application started successfully, the API documentation page will be displayed.

### Stop the Application

To stop the running application, press:

```text
Ctrl+C
```


## API Endpoints

### Health

```bash
curl -i http://localhost:8001/health \
  -H "x-dashboard-secret: change-me"
```

### Chat

```bash
curl -i -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -H "x-dashboard-secret: change-me" \
  -d '{"prompt":"Show order 100001"}'
```

The `x-dashboard-secret` value must match the one configured in both the backend and the dashboard env files.

## Response Contract

The backend always returns the same response shape to the dashboard:

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

When a request fails, the `error` object is populated and `success` is set to `false`.

## Testing

Run the backend test suite with:

```bash
.venv/bin/python -m pytest tests
```

Run a quick compile check with:

```bash
.venv/bin/python -m compileall app
```

## Notes

- The backend caches commercetools OAuth tokens in memory and refreshes them automatically before expiry.
- All commercetools communication stays inside this service.
- The dashboard only receives normalized JSON and the final response text.
