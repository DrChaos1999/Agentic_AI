import Chat from "./components/Chat.jsx";

export default function App() {
  return (
    <div className="flex flex-col h-screen">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-2">
          <span className="text-xl">🇮🇹</span>
          <h1 className="font-semibold text-gray-800">Benvenuto</h1>
          <span className="text-sm text-gray-400">· AI guide for students in Italy</span>
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        <Chat />
      </main>
    </div>
  );
}
