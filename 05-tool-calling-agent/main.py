"""A minimal but real agent: an OpenAI model + tools in a loop.

The agent loop is THE core pattern behind every AI agent product:
  1. Send conversation + tool definitions to the model.
  2. If the reply contains tool_calls: run them locally, append the results
     as role="tool" messages, go to 1.
  3. Otherwise the model has its final answer -> return it.
"""
import ast
import datetime
import json
import operator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()
client = OpenAI()
MODEL = "gpt-4o-mini"
app = FastAPI()

# ---------------- Tool implementations ----------------
FAKE_WEATHER = {  # stand-in for a real weather API call
    "tokyo": "27°C, humid, light rain expected this evening",
    "london": "16°C, overcast with drizzle",
    "dhaka": "33°C, hot and humid, chance of thunderstorms",
    "new york": "22°C, clear skies",
}

_ALLOWED_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
                ast.Mult: operator.mul, ast.Div: operator.truediv,
                ast.Pow: operator.pow, ast.USub: operator.neg}


def safe_calc(expression: str) -> str:
    """Evaluate arithmetic safely by walking the AST — never use eval()
    on model output."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](walk(node.operand))
        raise ValueError("Unsupported expression")
    try:
        return str(walk(ast.parse(expression, mode="eval")))
    except Exception as e:
        return f"calc error: {e}"


def get_weather(city: str) -> str:
    return FAKE_WEATHER.get(city.lower().strip(),
                            f"No data for {city} (demo only knows: {', '.join(FAKE_WEATHER)})")


def get_time() -> str:
    return datetime.datetime.now().strftime("%A %d %B %Y, %H:%M")


TOOLS = [
    {"type": "function", "function": {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression like '245 * 0.18'.",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string"}},
                       "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "parameters": {"type": "object",
                       "properties": {"city": {"type": "string"}},
                       "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "get_time",
        "description": "Get the current local date and time.",
        "parameters": {"type": "object", "properties": {}}}},
]

TOOL_FUNCS = {
    "calculator": lambda args: safe_calc(args["expression"]),
    "get_weather": lambda args: get_weather(args["city"]),
    "get_time": lambda args: get_time(),
}


class AgentRequest(BaseModel):
    question: str


@app.post("/api/agent")
def run_agent(req: AgentRequest):
    messages = [{"role": "user", "content": req.question}]
    trace = []  # tool calls, shown in the UI

    for _ in range(6):  # hard cap: never let an agent loop forever
        resp = client.chat.completions.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages,
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return {"answer": msg.content or "", "trace": trace}

        # Model asked for tools: run them and feed results back.
        messages.append(msg)  # the assistant turn containing tool_calls
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            output = TOOL_FUNCS[tc.function.name](args)
            trace.append({"tool": tc.function.name, "input": args,
                          "output": output})
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": output})

    return {"answer": "Agent hit the step limit.", "trace": trace}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
