import { useState, useRef } from "react";
import { Mic, Square } from "lucide-react";
import { sendVoice } from "../api.js";

export default function VoiceButton({ onResult }) {
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const rec = new MediaRecorder(stream);
    chunksRef.current = [];
    rec.ondataavailable = (e) => chunksRef.current.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      const data = await sendVoice(blob);
      onResult(data); // { transcript, answer, tools_used }
    };
    rec.start();
    recorderRef.current = rec;
    setRecording(true);
  }

  function stop() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  return (
    <button
      onClick={recording ? stop : start}
      title={recording ? "Stop recording" : "Ask by voice"}
      className={`p-2.5 rounded-full border transition ${
        recording
          ? "bg-red-500 text-white border-red-500 animate-pulse"
          : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
      }`}
    >
      {recording ? <Square size={18} /> : <Mic size={18} />}
    </button>
  );
}
