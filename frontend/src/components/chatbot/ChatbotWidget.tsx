"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X } from "lucide-react";
import { ChatbotCard } from "./ChatbotCard";
import { Analysis } from "@/lib/types";
import "./chatbot.css";

interface ChatbotWidgetProps {
  analysis: Analysis;
}

export const ChatbotWidget: React.FC<ChatbotWidgetProps> = ({ analysis }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-[60] flex flex-col items-end gap-3">
      <AnimatePresence>
        {isOpen && (
          <ChatbotCard onClose={() => setIsOpen(false)} analysis={analysis} />
        )}
      </AnimatePresence>

      {/* FAB */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => setIsOpen((v) => !v)}
        aria-label={isOpen ? "Close AI assistant" : "Open AI assistant"}
        className={`
          relative w-14 h-14 rounded-2xl flex items-center justify-center
          shadow-[0_8px_32px_-8px_hsl(222_47%_14%/0.35)]
          transition-all duration-300
          ${isOpen
            ? "bg-[hsl(222_47%_14%)] border border-[hsl(222_47%_22%)]"
            : "bg-[hsl(14_78%_52%)] animate-chatbot-pulse"
          }
        `}
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.span
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0,   opacity: 1 }}
              exit={{   rotate:  90,  opacity: 0 }}
              transition={{ duration: 0.18 }}
            >
              <X className="w-6 h-6 text-[hsl(40_30%_98%)]" />
            </motion.span>
          ) : (
            <motion.span
              key="open"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0,  opacity: 1 }}
              exit={{   rotate: -90, opacity: 0 }}
              transition={{ duration: 0.18 }}
            >
              <Sparkles className="w-6 h-6 text-white chatbot-glow" />
            </motion.span>
          )}
        </AnimatePresence>

        {/* Notification dot */}
        {!isOpen && (
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-[hsl(222_47%_14%)] border-2 border-[hsl(40_30%_98%)]" />
        )}
      </motion.button>
    </div>
  );
};
