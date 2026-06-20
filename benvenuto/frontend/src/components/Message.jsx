import ToolBadge from "./ToolBadge.jsx";

export default function Message({ role, text, tools }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 whitespace-pre-wrap leading-relaxed ${
          isUser
            ? "bg-emerald-600 text-white rounded-br-sm"
            : "bg-white text-gray-800 border border-gray-200 rounded-bl-sm"
        }`}
      >
        {!isUser && tools?.length > 0 && (
          <div className="mb-1.5">
            {tools.map((t, i) => (
              <ToolBadge key={i} name={t} />
            ))}
          </div>
        )}
        {text || (!isUser && <span className="text-gray-400">…</span>)}
      </div>
    </div>
  );
}
