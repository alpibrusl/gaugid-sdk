# Gaugid Cross-Agent Demo — Three Agents, One Profile

A live demo showing the core Gaugid value proposition:
**your AI context follows you across ANY agent, and YOU control it.**

## What it demonstrates

Three different AI agents (different frameworks, different providers) share a single user profile through Gaugid:

1. **Travel Agent** (Google ADK + Gemini) learns your travel preferences
2. **Food Agent** (LangGraph + Gemini) *already knows* your dietary preferences without being told
3. **Personal Assistant** (Anthropic Claude) sees *everything* — travel + food + all other memories

Between each agent, you open the Gaugid dashboard to approve/reject memory proposals. This is the "aha moment": portable AI memory, owned by the user.

## Quick start

```bash
# 1. Set required environment variable
export GAUGID_CONNECTION_TOKEN=gaugid_conn_xxx  # Get from dashboard.gaugid.com

# 2. (Optional) Set AI API keys for real responses
export GOOGLE_API_KEY=your-google-api-key
export ANTHROPIC_API_KEY=your-anthropic-api-key

# 3. Install dependencies
pip install gaugid google-generativeai langchain-google-genai anthropic

# 4. Run the demo
python demo_runner.py
```

Without API keys, the demo uses simulated AI responses — the Gaugid profile sharing still works exactly the same way.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GAUGID_CONNECTION_TOKEN` | Yes | Connection token from [dashboard.gaugid.com](https://dashboard.gaugid.com) |
| `GOOGLE_API_KEY` | No | Google API key for Gemini (Travel & Food agents) |
| `ANTHROPIC_API_KEY` | No | Anthropic API key for Claude (Assistant agent) |
| `GAUGID_API_URL` | No | Custom API URL (defaults to production) |

## Demo flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Travel Agent   │     │    Food Agent     │     │    Assistant     │
│   (Google ADK)   │     │   (LangGraph)     │     │   (Anthropic)   │
└────────┬─────────┘     └────────┬──────────┘     └────────┬─────────┘
         │                        │                         │
    proposes memories        reads profile             reads profile
    about travel prefs    (sees travel prefs!)      (sees EVERYTHING!)
         │                  proposes food prefs              │
         ▼                        ▼                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Gaugid Profile (a2p-cloud)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐               │
│  │ Travel prefs │  │ Food prefs  │  │ Other context │               │
│  └─────────────┘  └─────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                    ┌─────────┴─────────┐
                    │  Gaugid Dashboard  │
                    │  (user approves/   │
                    │   rejects memories)│
                    └───────────────────┘
```

## Files

| File | Description |
|---|---|
| `demo_runner.py` | Main entry point — orchestrates the full demo flow |
| `demo_config.py` | Shared configuration, terminal colors, and formatting utilities |
| `agent_travel.py` | Travel Agent using Google Gemini + Gaugid |
| `agent_food.py` | Food Agent using LangChain/Gemini + Gaugid |
| `agent_assistant.py` | Personal Assistant using Anthropic Claude + Gaugid |

## How it works

Each agent creates a `GaugidClient` with the same connection token. The connection token is tied to a specific user profile in the Gaugid cloud:

```python
from gaugid import GaugidClient

client = GaugidClient(connection_token="gaugid_conn_xxx")

# Read profile (including memories from other agents)
profile = await client.get_profile(scopes=["a2p:travel.*", "a2p:food.*"])

# Propose new memories (user must approve via dashboard)
await client.propose_memory(
    content="Prefers window seats on flights",
    category="a2p:travel.seats",
    memory_type="semantic",
    confidence=0.85,
)
```

The key principle: agents **propose** memories, but the **user approves** them. This is consent-first AI personalization.

## Recording the demo

For a screen recording:

1. Open two windows side-by-side: terminal + Gaugid dashboard
2. Run `python demo_runner.py` in the terminal
3. When prompted, switch to the dashboard to show approve/reject flow
4. The terminal output is color-coded and formatted for readability
