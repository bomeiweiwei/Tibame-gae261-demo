# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A Flask web app that demonstrates a multi-agent architecture (built on Microsoft's `agent_framework`, using an Azure OpenAI-compatible chat client) for a resort assistant. A user submits a free-text question through the web form; it is routed to one or more specialized sub-agents (weather, traffic, resort QA) whose tool calls currently return stubbed/mock data (no real RAG store or traffic API is wired up yet).

## Running the app

```bash
pip install -r requirements.txt
python app.py
```

The app reads config from `.env` (copy `.env.example` to `.env` and fill in `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`, `OPEN_WEATHER_MAP_API_KEY`). It serves at the Flask default port with `DEBUG` controlled by the `DEBUG` env var.

There is no test suite, linter, or build step configured in this repo.

## Architecture

**Request flow:** `app.py` (`/submit` route) → `agents/main_agent_tool_service.route_question()` → Azure OpenAI-backed `main_agent` → sub-agents exposed to it as callable "tools" via `agent.as_tool(...)` → each sub-agent calls its own plain-Python `@tool`-decorated function in `tools/`.

There are **two parallel implementations of the routing agent** — only one is active:
- `agents/main_agent_tool_service.py` (active — imported by `app.py`): an LLM-driven router. `main_agent` is given three sub-agents wrapped as tools (`WeatherLookup`, `TrafficLookup`, `ResortQALookup`) and decides itself, via its system prompt, which to call and how to merge their text responses.
- `agents/main_agent_service.py` (unused, import commented out in `app.py`): a keyword-based router (`is_weather_question`, `is_traffic_question`, `is_resort_qa_question` string-matching on Chinese keywords) that calls sub-agent functions directly and concatenates results under Chinese section headers. Note this file imports `run_resort_qa_agent` from `resort_qa_agent_service.py`, but that function doesn't currently exist there — this path is broken if re-enabled.

When modifying routing logic, check which of these two files is actually wired up in `app.py` before assuming your change takes effect.

**Sub-agent layer** (`agents/weather_agent_service.py`, `agents/traffic_agent_service.py`, `agents/resort_qa_agent_service.py`): each constructs its own `OpenAIChatClient(...).as_agent(instructions=..., tools=[...])` scoped to one domain, with a Traditional-Chinese system prompt that strictly forbids the agent from answering from its own knowledge — it must only relay whatever its tool function returns (including literal "not yet wired to a real API" stub text). This constraint is intentional and enforced through the prompt, not through code — preserve it when editing instructions.

**Tool layer** (`tools/weather_tools.py`, `tools/traffic_tools.py`, `tools/rag_tools.py`): plain functions decorated with `@tool(name=..., description=...)` from `agent_framework`, each returning a `dict` with `status` + `report` (or `error_message`). `weather_tools.get_weather` is the only one that calls a real external API (OpenWeatherMap); `traffic_tools.query_traffic` and all four functions in `rag_tools.py` (`query_facility_hours`, `query_attraction_hours`, `query_rules`, `query_restaurant_food`) are stubs that just echo the input back with a "not yet connected to a real API/RAG store" message. When wiring up real data sources, replace the body of these stub functions while keeping the `@tool` signature (name/description/arg annotations) intact, since the agent's tool-selection depends on those descriptions.

**Frontend**: a single Jinja2 template (`templates/index.html`) with an inline `<style>` block — a plain form posting to `/submit`, rendering `result` back into the same page. No separate JS/CSS assets or build pipeline.

All agent instructions and routing keywords are in Traditional Chinese (zh-Hant); keep new prompts/keywords consistent with that when extending the resort domain.
