"use client";

import React from "react";
import { motion } from "framer-motion";

interface ChatMessageProps {
  role: "user" | "bot";
  content: string;
  isTyping?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, isTyping }) => {
  const isBot = role === "bot";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex ${isBot ? "justify-start" : "justify-end"} mb-4 w-full`}
    >
      <div
        className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
          isBot
            ? "bg-[#F8FAFC] text-[#334155] rounded-bl-none border border-[#E2E8F0] shadow-sm"
            : "bg-[#4F8EF7] text-white rounded-br-none shadow-md shadow-blue-500/10"
        }`}
      >
        {isTyping ? (
          <div className="flex items-center space-x-1 py-1 px-2">
            <span className="dot-bounce"></span>
            <span className="dot-bounce"></span>
            <span className="dot-bounce"></span>
          </div>
        ) : (
          content
        )}
      </div>
    </motion.div>
  );
};
