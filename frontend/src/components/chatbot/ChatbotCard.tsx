"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, Sparkles, X, ShieldCheck, Trash2 } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { Analysis } from "@/lib/types";
import "./chatbot.css";

interface Message {
  role: "user" | "bot";
  content: string;
}

const SUGGESTED_CHIPS = [
  "Summarize the claims.",
  "Any contradictions?",
  "Explain the credibility score.",
  "What's the overall verdict?",
];

const buildContext = (analysis: Analysis) =>
  `Title: ${analysis.title}
Source: ${analysis.source}
Verdict: ${analysis.verdict}
Credibility Score: ${analysis.overallCredibility}/100
AI Confidence: ${analysis.overallConfidence}%
Summary: ${analysis.summary}
Reasoning: ${analysis.reasoning}
Claims:
${analysis.claims.map((c, i) => `${i + 1}. ${c.text} → ${c.verdict} (confidence ${c.confidence}%)`).join("\n")}
False details: ${analysis.falseDetails.join("; ") || "none"}
Uncertain details: ${analysis.uncertainDetails.join("; ") || "none"}`;

export const ChatbotCard: React.FC<{ onClose: () => void; analysis: Analysis }> = ({
  onClose,
  analysis,
}) => {
  const storageKey = `veritas-chat-${analysis.id}`;

  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? (JSON.parse(saved) as Message[]) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Persist to localStorage whenever messages change
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {
      // quota exceeded — silently fail
    }
  }, [messages, storageKey]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    setMessages((p) => [...p, { role: "user", content: text }]);
    setInput("");
    setIsTyping(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/chatbot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          article_context: buildContext(analysis),
        }),
      });
      const data = await res.json() as { reply: string };
      setMessages((p) => [...p, { role: "bot", content: data.reply }]);
    } catch {
      setMessages((p) => [
        ...p,
        {
          role: "bot",
          content: "Couldn't reach the AI right now. Please check if GEMINI_API_KEY is configured.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92, y: 20, originX: 1, originY: 1 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{   opacity: 0, scale: 0.92, y: 20 }}
      transition={{ type: "spring", stiffness: 340, damping: 28 }}
      className="
        w-[480px] h-[620px]
        flex flex-col rounded-2xl overflow-hidden
        bg-[hsl(40_30%_98%)] border border-[hsl(36_18%_86%)]
        shadow-[0_24px_64px_-12px_hsl(222_47%_14%/0.22),0_0_0_1px_hsl(36_18%_88%)]
      "
    >
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[hsl(36_18%_88%)] bg-[hsl(222_47%_14%)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[hsl(14_78%_52%)] flex items-center justify-center shadow-sm">
            <Sparkles className="w-5 h-5 text-white chatbot-glow" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[hsl(40_30%_96%)] font-sans tracking-tight">
              Article AI
            </h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <ShieldCheck className="w-3 h-3 text-[hsl(14_78%_62%)]" />
              <p className="text-[10px] text-[hsl(40_20%_70%)] font-mono uppercase tracking-widest">
                Bounded to this article
              </p>
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-white/10 text-[hsl(40_20%_70%)] hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            title="Clear conversation"
            className="p-1.5 rounded-lg hover:bg-white/10 text-[hsl(40_20%_70%)] hover:text-white transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>


      {/* ── Messages ── */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-1 custom-scrollbar bg-[hsl(40_30%_98%)]"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col justify-center items-center text-center px-6 gap-4">
            <div className="w-16 h-16 rounded-2xl bg-[hsl(36_22%_93%)] border border-[hsl(36_18%_86%)] flex items-center justify-center">
              <Bot className="w-8 h-8 text-[hsl(222_47%_30%)]" />
            </div>
            <div>
              <h4 className="font-serif text-lg font-semibold text-[hsl(222_35%_11%)] mb-1">
                Ask me anything
              </h4>
              <p className="text-sm text-[hsl(222_12%_42%)] leading-relaxed">
                I have full context on this article's claims, verdict, and evidence.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 mt-1">
              {SUGGESTED_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => void handleSend(chip)}
                  className="
                    px-3 py-1.5 text-xs font-medium rounded-full
                    border border-[hsl(36_18%_82%)] bg-white
                    text-[hsl(222_35%_22%)] hover:text-[hsl(14_78%_48%)]
                    hover:border-[hsl(14_78%_52%/0.4)] hover:bg-[hsl(14_78%_52%/0.04)]
                    transition-all active:scale-95
                  "
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}

        {isTyping && <ChatMessage role="bot" content="" isTyping />}
      </div>

      {/* ── Input ── */}
      <div className="px-4 py-3.5 border-t border-[hsl(36_18%_88%)] bg-[hsl(36_22%_97%)]">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void handleSend(input)}
            placeholder="Ask about this article…"
            className="
              flex-1 min-w-0 bg-white border border-[hsl(36_18%_84%)]
              rounded-xl py-3 px-4 text-sm text-[hsl(222_35%_11%)]
              placeholder:text-[hsl(222_12%_58%)]
              focus:outline-none focus:border-[hsl(222_47%_30%)]
              focus:ring-3 focus:ring-[hsl(222_47%_14%/0.08)]
              transition-all shadow-sm
            "
          />
          <button
            onClick={() => void handleSend(input)}
            disabled={!input.trim() || isTyping}
            className={`
              shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all
              ${input.trim() && !isTyping
                ? "bg-[hsl(14_78%_52%)] text-white shadow-[0_4px_12px_-4px_hsl(14_78%_52%/0.5)] hover:bg-[hsl(14_78%_48%)] active:scale-90"
                : "bg-[hsl(36_22%_90%)] text-[hsl(222_12%_62%)] cursor-not-allowed"
              }
            `}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};
