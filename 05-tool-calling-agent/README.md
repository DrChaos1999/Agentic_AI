# 05 — Tool-Calling Agent

Ask things like *"What's the weather in Tokyo, and what's 18% of 245?"* —
the agent decides which tools to call, calls them (possibly several in a row),
and composes a final answer. The UI shows every tool call so you can watch the
agent think.

**Techniques:** function/tool calling, the **agent loop** (model → tool →
results back to model → repeat until `stop_reason != "tool_use"`), tool schemas,
safe tool implementations.

Run: install deps, copy `.env.example` → `.env`, `python main.py`,
open http://localhost:8000
