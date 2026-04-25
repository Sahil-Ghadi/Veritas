"use client";

import { useState, useEffect } from "react";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { AnalysisInput } from "@/components/AnalysisInput";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { AnalysisResult } from "@/components/AnalysisResult";
import { getAnalysisById, pollAnalysisUntilDone, startAnalysis, getAllAnalyses } from "@/lib/api";
import { Analysis } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { AlertTriangle, Sparkles, Search, BrainCircuit, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "result"; analysis: Analysis; cached: boolean }
  | { kind: "error"; message: string };

const Analyze = () => {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [pipelineStep, setPipelineStep] = useState("Queued");

  const handleAnalyze = async (mode: "url" | "text" | "image", value: string) => {
    try {
      const queued = await startAnalysis({ input_type: mode, raw_input: value });
      setState({ kind: "loading" });
      setPipelineStep("Queued");
      const done = await pollAnalysisUntilDone(queued.job_id, 400, (progress) => {
        if (progress.step) setPipelineStep(progress.step);
      });
      if (done.status === "error") {
        setState({
          kind: "error",
          message: done.error
            ? `${done.error}${done.step ? ` (at: ${done.step})` : ""}`
            : "Analysis failed.",
        });
        return;
      }

      const analysis = await getAnalysisById(queued.job_id);
      if (!analysis) {
        setState({ kind: "error", message: "Could not load analysis result." });
        return;
      }
      setState({ kind: "result", analysis, cached: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error occurred.";
      setState({ kind: "error", message });
    }
  };

  const reset = () => {
    setPipelineStep("Queued");
    setState({ kind: "idle" });
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <NavigationSidebar />

      <div className="flex flex-1 min-w-0">
        <main className="flex-1 min-w-0 flex flex-col">
          <div className={`container max-w-4xl py-8 md:py-12 flex-1 flex flex-col ${state.kind === "idle" ? "justify-center min-h-[85vh]" : ""}`}>
            {state.kind === "idle" && (
              <div className="w-full xl:-mt-8">
                <div className="mb-8 animate-fade-in-up">
                  <p className="text-xs font-mono uppercase tracking-widest text-accent mb-2">New Analysis</p>
                  <h1 className="font-display text-4xl md:text-5xl italic font-light tracking-tightest text-balance">
                    What do you want to <span className="italic font-light">verify?</span>
                  </h1>
                  <p className="text-muted-foreground mt-3 text-lg">
                    Drop a link, paste text, or upload an image. We'll do the rest.
                  </p>
                </div>

                <AnalysisInput onAnalyze={handleAnalyze} loading={false} />

                {/* Feature Highlights */}
                <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <Card className="p-6 bg-gradient-card border-border/40 hover:border-primary/30 transition-colors shadow-sm">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                      <Search className="h-5 w-5 text-primary" />
                    </div>
                    <h3 className="font-semibold mb-2 text-foreground/90">Deep Web Search</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">Scans thousands of reliable sources to find confirming or contradicting evidence in real-time.</p>
                  </Card>
                  <Card className="p-6 bg-gradient-card border-border/40 hover:border-primary/30 transition-colors shadow-sm">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                      <BrainCircuit className="h-5 w-5 text-primary" />
                    </div>
                    <h3 className="font-semibold mb-2 text-foreground/90">AI Analysis</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">Breaks down complex articles into atomic claims and evaluates their credibility instantly.</p>
                  </Card>
                  <Card className="p-6 bg-gradient-card border-border/40 hover:border-primary/30 transition-colors shadow-sm">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                      <ShieldCheck className="h-5 w-5 text-primary" />
                    </div>
                    <h3 className="font-semibold mb-2 text-foreground/90">Community Driven</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">Transparent results that can be audited, disputed, and refined by the community.</p>
                  </Card>
                </div>
              </div>
            )}

            {state.kind === "loading" && (
              <div>
                <div className="mb-6 animate-fade-in">
                  <h1 className="font-serif text-2xl md:text-3xl font-semibold flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary animate-pulse" /> Analyzing
                  </h1>
                </div>
                <AnalysisProgress currentStep={pipelineStep} />
              </div>
            )}

            {state.kind === "error" && (
              <Card className="p-6 border-destructive/40 bg-destructive/5">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
                  <div>
                    <p className="font-semibold text-destructive">Analysis failed</p>
                    <p className="text-sm text-muted-foreground mt-1">{state.message}</p>
                    <Button variant="outline" size="sm" className="mt-3" onClick={reset}>Try again</Button>
                  </div>
                </div>
              </Card>
            )}

            {state.kind === "result" && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <Button variant="ghost" size="sm" onClick={reset}>← New analysis</Button>
                  <span className="text-xs font-mono text-muted-foreground">analysis #{state.analysis.id}</span>
                </div>
                <AnalysisResult analysis={state.analysis} cached={state.cached} />
              </div>
            )}
          </div>
        </main>
        <ActivitySidebar analysis={state.kind === "result" ? state.analysis : undefined} />
      </div>
    </div>
  );
};

export default Analyze;
