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
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 380, damping: 30 }}
      className={`flex ${isBot ? "justify-start" : "justify-end"} mb-3 w-full`}
    >
      <div
        className={`
          max-w-[82%] px-4 py-2.5 text-sm leading-relaxed
          ${isBot
            ? `rounded-2xl rounded-bl-sm
               bg-white border border-[hsl(36_18%_86%)]
               text-[hsl(222_35%_11%)]
               shadow-[0_1px_4px_hsl(222_47%_14%/0.06)]`
            : `rounded-2xl rounded-br-sm
               bg-[hsl(14_78%_52%)] text-white
               shadow-[0_4px_12px_-4px_hsl(14_78%_52%/0.4)]`
          }
        `}
      >
        {isTyping ? (
          <div className="flex items-center gap-0.5 py-1 px-1">
            <span className="dot-bounce" />
            <span className="dot-bounce" />
            <span className="dot-bounce" />
          </div>
        ) : (
          content
        )}
      </div>
    </motion.div>
  );
};
