import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import Message from "./Message.jsx";
import VoiceButton from "./VoiceButton.jsx";
import { streamChat } from "../api.js";

const SUGGESTIONS = [
  "Can I travel in the EU while my permesso is pending?",
  "Top spots in Venice and what scams to avoid?",
  "Where can I buy basmati rice near Politecnico di Milano?",
  "How do I greet my professor for the first time?",
];

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setBusy(true);

    const history = messages.map((m) => ({ role: m.role, content: m.text }));
    setMessages((m) => [...m, { role: "user", text: q }]);
    // placeholder assistant message we stream into
    setMessages((m) => [...m, { role: "assistant", text: "", tools: [] }]);

    try {
      await streamChat(
        q,
        history,
        (chunk) =>
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = {
              ...copy[copy.length - 1],
              text: copy[copy.length - 1].text + chunk,
            };
            return copy;
          }),
        (tools) =>
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { ...copy[copy.length - 1], tools };
            return copy;
          })
      );
    } catch (e) {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = {
          role: "assistant",
          text: "⚠️ Couldn't reach the server. Is the backend running on :8000?",
          tools: [],
        };
        return copy;
      });
    } finally {
      setBusy(false);
    }
  }

  function onVoiceResult(data) {
    setMessages((m) => [
      ...m,
      { role: "user", text: data.transcript },
      { role: "assistant", text: data.answer, tools: data.tools_used || [] },
    ]);
  }

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto w-full">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            <p className="text-lg mb-4">Ask me anything about living &amp; studying in Italy 🇮🇹</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => send(s)}
                  className="text-sm px-3 py-1.5 rounded-full bg-white border border-gray-200 hover:border-emerald-400 hover:text-emerald-700"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <Message key={i} role={m.role} text={m.text} tools={m.tools} />
        ))}
        <div ref={endRef} />
      </div>

      <div className="border-t bg-white px-4 py-3">
        <div className="flex items-center gap-2 max-w-2xl mx-auto">
          <VoiceButton onResult={onVoiceResult} />
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Type your question…"
            className="flex-1 px-4 py-2.5 rounded-full border border-gray-300 focus:outline-none focus:border-emerald-500"
          />
          <button
            onClick={() => send()}
            disabled={busy}
            className="p-2.5 rounded-full bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
