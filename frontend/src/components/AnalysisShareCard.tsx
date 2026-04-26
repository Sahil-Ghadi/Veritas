"use client";

import { Analysis } from "@/lib/types";
import { Card } from "./ui/card";
import { VerdictBadge } from "./VerdictBadge";
import { Shield, Sparkles } from "lucide-react";
import { CredibilityMeter } from "./CredibilityMeter";
import { cn } from "@/lib/utils";

interface AnalysisShareCardProps {
  analysis: Analysis;
  className?: string;
}

export const AnalysisShareCard = ({ analysis, className }: AnalysisShareCardProps) => {
  return (
    <div 
      id={className?.includes("capture") ? "analysis-share-card" : undefined}
      className={cn("p-8 bg-background relative overflow-hidden border border-border", className)}
      style={{ 
        background: "linear-gradient(135deg, hsl(var(--background)) 0%, hsl(var(--secondary)/0.3) 100%)",
      }}
    >
      {/* Decorative background elements */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-accent/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
      
      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <span className="font-serif text-xl font-bold tracking-tight">Veritas</span>
          </div>
          <div className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground uppercase tracking-widest bg-secondary/50 px-2 py-1 rounded border border-border/40">
            <Sparkles className="h-3 w-3 text-primary" /> Verified Analysis
          </div>
        </div>

        {/* Verdict */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-4">
            <VerdictBadge verdict={analysis.verdict} size="lg" />
            <div className="h-px flex-1 bg-border/40" />
          </div>
          <h2 className="font-serif text-2xl font-bold leading-tight text-foreground">
            {analysis.title}
          </h2>
          <p className="mt-2 text-xs text-muted-foreground font-mono">
            Source: {analysis.source}
          </p>
        </div>

        {/* Summary snippet */}
        <div className="mb-8 p-4 bg-background/40 border border-border/40 rounded-xl">
           <p className="text-sm text-foreground/80 leading-relaxed italic">
             "{analysis.summary}"
           </p>
        </div>

        {/* Metrics */}
        <div className="mt-auto grid grid-cols-2 gap-6">
          <CredibilityMeter score={analysis.overallCredibility} label="Credibility" size="md" />
          <CredibilityMeter score={analysis.overallConfidence} label="AI Confidence" size="md" />
        </div>

        {/* Footer / Watermark */}
        <div className="mt-10 pt-4 border-t border-border/40 flex items-center justify-between">
           <p className="text-[10px] text-muted-foreground font-mono">
             REF: {analysis.id.slice(0, 8).toUpperCase()}
           </p>
           <p className="text-[10px] text-primary/60 font-serif italic">
             veritas-news.app
           </p>
        </div>
      </div>
    </div>
  );
};
