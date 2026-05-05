"use client";

import { useState } from "react";
import Chat from "./components/Chat";
import Eval from "./components/Eval";

type Tab = "chat" | "eval";

export default function Home() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="min-h-screen bg-nyvia-dark flex flex-col">
      {/* Tab bar */}
      <div className="border-b border-nyvia-border bg-nyvia-dark sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 flex gap-1 pt-3">
          {(["chat", "eval"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-t-lg text-sm font-medium transition-all ${
                tab === t
                  ? "bg-nyvia-surface border border-b-0 border-nyvia-border text-white"
                  : "text-nyvia-muted hover:text-white"
              }`}
            >
              {t === "chat" ? "Chat" : "Evaluación"}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1">
        {tab === "chat" ? <Chat /> : <Eval />}
      </div>
    </div>
  );
}
