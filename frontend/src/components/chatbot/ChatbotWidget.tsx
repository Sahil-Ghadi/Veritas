"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye } from "lucide-react";
import { ChatbotCard } from "./ChatbotCard";

export const ChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-[60]">
      <AnimatePresence>
        {isOpen && (
          <ChatbotCard onClose={() => setIsOpen(false)} />
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full flex items-center justify-center transition-all shadow-2xl relative ${
          isOpen ? "bg-[#1A1D27] border border-[#2D313E]" : "bg-[#4F8EF7] animate-chatbot-pulse"
        }`}
      >
        <Eye 
          className={`w-7 h-7 transition-colors ${
            isOpen ? "text-[#4F8EF7]" : "text-white"
          } chatbot-glow`} 
        />
        {!isOpen && (
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 border-2 border-[#0F1117] rounded-full"></div>
        )}
      </motion.button>
    </div>
  );
};
