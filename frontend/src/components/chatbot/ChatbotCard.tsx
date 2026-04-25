"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, X, Bot, Sparkles } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import "./chatbot.css";

interface Message {
  role: "user" | "bot";
  content: string;
}

const SUGGESTED_CHIPS = [
  "How does claim-level scoring work?",
  "Explain Temporal Drift.",
  "How to use the WhatsApp bot?",
  "What is Credibility DNA?",
];

export const ChatbotCard: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chatbot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json();
      
      const botMsg: Message = { role: "bot", content: data.reply };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "Sorry, I'm having trouble connecting to my brain. Is Ollama running?" },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 100, x: 100, originX: 1, originY: 1 }}
      animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
      exit={{ opacity: 0, scale: 0.8, y: 100, x: 100 }}
      className="fixed bottom-24 right-6 w-[380px] h-[540px] bg-white border border-[#E2E8F0] rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.1)] z-50 flex flex-col overflow-hidden"
    >
      {/* Header */}
      <div className="p-5 border-b border-[#F1F5F9] bg-white flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-2xl bg-[#EEF2FF] flex items-center justify-center border border-[#E0E7FF]">
            <Sparkles className="w-6 h-6 text-[#4F8EF7] chatbot-glow" />
          </div>
          <div>
            <h3 className="text-[15px] font-bold text-[#1E293B]">VeritAI Assistant</h3>
            <div className="flex items-center space-x-1.5">
              <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></div>
              <p className="text-[10px] text-[#64748B] font-bold tracking-wider uppercase">Local RAG Agent</p>
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-xl hover:bg-[#F8FAFC] text-[#94A3B8] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 custom-scrollbar" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="h-full flex flex-col justify-center items-center text-center px-6">
            <div className="w-20 h-20 rounded-[2rem] bg-[#F8FAFC] flex items-center justify-center mb-5 border border-[#F1F5F9]">
              <Bot className="w-10 h-10 text-[#4F8EF7]" />
            </div>
            <h4 className="text-[#1E293B] font-bold mb-2 text-xl">How can I help?</h4>
            <p className="text-[#64748B] text-sm mb-8 leading-relaxed">
              Ask me anything about how VeritAI fact-checks news and detects manipulation.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => handleSend(chip)}
                  className="px-4 py-2 bg-white hover:bg-[#F8FAFC] text-[#4F8EF7] text-xs font-semibold rounded-xl border border-[#E2E8F0] shadow-sm transition-all active:scale-95"
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
        {isTyping && <ChatMessage role="bot" content="" isTyping={true} />}
      </div>

      {/* Input */}
      <div className="p-5 bg-white">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
            placeholder="Type a message..."
            className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-[1.25rem] py-4 pl-5 pr-14 text-sm text-[#334155] placeholder-[#94A3B8] focus:outline-none focus:border-[#4F8EF7] focus:ring-4 focus:ring-[#4F8EF7]/5 transition-all shadow-inner"
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim()}
            className={`absolute right-2.5 p-2.5 rounded-xl transition-all ${
              input.trim()
                ? "bg-[#4F8EF7] text-white shadow-lg shadow-blue-500/20 active:scale-90"
                : "text-[#CBD5E1] cursor-not-allowed"
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};
