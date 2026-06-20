const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// Streams the agent's answer. Calls onTools(names[]) and onChunk(text) as events arrive.
export async function streamChat(message, history, onChunk, onTools) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok || !res.body) throw new Error(`Server error ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      let evt;
      try { evt = JSON.parse(line.slice(5).trim()); } catch { continue; }
      if (evt.type === "tools") onTools(evt.tools);
      else if (evt.type === "token") onChunk(evt.text);
    }
  }
}

// Sends a recorded audio blob to Whisper-backed /voice.
export async function sendVoice(blob) {
  const form = new FormData();
  form.append("file", blob, "question.webm");
  const res = await fetch(`${BASE}/voice`, { method: "POST", body: form });
  return res.json();
}

// Plays a phrase aloud via the TTS endpoint.
export async function speak(text, voice = "alloy") {
  const res = await fetch(`${BASE}/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  const buf = await res.arrayBuffer();
  const url = URL.createObjectURL(new Blob([buf], { type: "audio/mpeg" }));
  new Audio(url).play();
}
