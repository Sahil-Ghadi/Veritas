"use client";

import { useState } from "react";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { AnalysisInput } from "@/components/AnalysisInput";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { AnalysisResult } from "@/components/AnalysisResult";
import { mockAnalyses } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Sparkles, FileText, Image as ImageIcon, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "result"; analysisId: string; cached: boolean };

const Analyze = () => {
  const [state, setState] = useState<State>({ kind: "idle" });

  const handleAnalyze = (mode: "url" | "text" | "image", value: string) => {
    // Simulate "already analyzed" detection
    const alreadyExists = mode === "url" && value.toLowerCase().includes("coffee");
    setState({ kind: "loading" });
    // The progress component drives onComplete
    // Store choice for after completion
    (handleAnalyze as any).cached = alreadyExists;
  };

  const completeAnalysis = () => {
    const cached = (handleAnalyze as any).cached || false;
    setState({ kind: "result", analysisId: "a1", cached });
  };

  const reset = () => setState({ kind: "idle" });

  const result = state.kind === "result" ? mockAnalyses.find((a) => a.id === state.analysisId)! : null;

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <NavigationSidebar />

      <div className="flex flex-1 min-w-0">
        <main className="flex-1 min-w-0">
          <div className="container max-w-4xl py-8 md:py-12">
            {state.kind === "idle" && (
              <>
                <div className="mb-8 animate-fade-in-up">
                  <p className="text-xs font-mono uppercase tracking-widest text-accent mb-2">— New Analysis</p>
                  <h1 className="font-display text-4xl md:text-5xl font-medium tracking-tightest text-balance">
                    What do you want to <span className="italic font-light">verify?</span>
                  </h1>
                  <p className="text-muted-foreground mt-3 text-lg">
                    Drop a link, paste text, or upload an image. We'll do the rest.
                  </p>
                </div>

                <AnalysisInput onAnalyze={handleAnalyze} />

                {/* Stats strip */}
                <Card className="mt-10 p-5 bg-gradient-card border-border/60 grid grid-cols-3 gap-4">
                  {[
                    { v: "12,847", l: "stories analyzed" },
                    { v: "2.4M", l: "claims checked" },
                    { v: "98.2%", l: "transparency rate" },
                  ].map((s, i) => (
                    <div key={i} className="text-center">
                      <p className="font-serif text-2xl font-semibold gradient-text">{s.v}</p>
                      <p className="text-xs text-muted-foreground mt-1">{s.l}</p>
                    </div>
                  ))}
                </Card>
              </>
            )}

            {state.kind === "loading" && (
              <div>
                <div className="mb-6 animate-fade-in">
                  <h1 className="font-serif text-2xl md:text-3xl font-semibold flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary animate-pulse" /> Analyzing
                  </h1>
                </div>
                <AnalysisProgress onComplete={completeAnalysis} />
              </div>
            )}

            {state.kind === "result" && result && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <Button variant="ghost" size="sm" onClick={reset}>← New analysis</Button>
                  <span className="text-xs font-mono text-muted-foreground">analysis #{result.id}</span>
                </div>
                <AnalysisResult analysis={result} cached={state.cached} />
              </div>
            )}
          </div>
        </main>
        <ActivitySidebar />
      </div>
    </div>
  );
};

export default Analyze;
