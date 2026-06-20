"""The orchestrator: a streaming function-calling loop.

gpt-4o sees all tool schemas, decides which to call, we run them, feed results
back, and repeat until it streams a final answer. Moderation gates the input.
"""
import json
from app.llm import client, moderate
from app.tools import TOOL_SCHEMAS, TOOL_REGISTRY
from app.config import settings

SYSTEM_PROMPT = """You are Benvenuto, an AI guide for international students in Italy.
Decide which tool(s) answer the user's question, call them, then write a clear,
friendly answer grounded ONLY in the tool results.

Rules:
- Prefer tools over your own memory for facts, prices, locations, news, and law.
- For legal or official-process answers, always add: "Verify with the official source
  (Questura / Prefettura / your university office) before acting."
- Cite the sources the tools return.
- If tools return nothing useful, say so honestly instead of inventing details.
- Be concise and practical. Use short paragraphs or tight bullet lists."""

MAX_STEPS = 5


async def stream_agent(user_message: str, history: list[dict]):
    """Async generator yielding {"type": "tools"|"token", ...} events."""
    if await moderate(user_message):
        yield {"type": "token", "text": "I can't help with that request."}
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history,
                {"role": "user", "content": user_message}]

    for _ in range(MAX_STEPS):
        stream = await client.chat.completions.create(
            model=settings.MODEL_ORCHESTRATOR,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            stream=True,
        )

        tool_calls: dict[int, dict] = {}
        content_parts: list[str] = []

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                content_parts.append(delta.content)
                yield {"type": "token", "text": delta.content}
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    slot = tool_calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function and tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        slot["args"] += tc.function.arguments

        # No tool calls this round -> the answer was already streamed.
        if not tool_calls:
            return

        # Re-assemble the assistant turn (with its tool calls) for the history.
        messages.append({
            "role": "assistant",
            "content": "".join(content_parts) or None,
            "tool_calls": [{
                "id": t["id"], "type": "function",
                "function": {"name": t["name"], "arguments": t["args"] or "{}"},
            } for t in tool_calls.values()],
        })

        # Tell the UI which tools fired, then execute them.
        yield {"type": "tools", "tools": [t["name"] for t in tool_calls.values()]}
        for t in tool_calls.values():
            try:
                args = json.loads(t["args"] or "{}")
                result = await TOOL_REGISTRY[t["name"]](**args)
            except Exception as e:  # never let one tool crash the turn
                result = {"error": f"{type(e).__name__}: {e}"}
            messages.append({
                "role": "tool",
                "tool_call_id": t["id"],
                "content": json.dumps(result, ensure_ascii=False)[:8000],
            })

    # Loop exhausted -> force one final, streamed synthesis with no more tools.
    final = await client.chat.completions.create(
        model=settings.MODEL_ORCHESTRATOR, messages=messages, stream=True
    )
    async for chunk in final:
        if chunk.choices and chunk.choices[0].delta.content:
            yield {"type": "token", "text": chunk.choices[0].delta.content}
