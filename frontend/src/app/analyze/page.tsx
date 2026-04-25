"use client";

import { useState } from "react";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { AnalysisInput } from "@/components/AnalysisInput";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { AnalysisResult } from "@/components/AnalysisResult";
import { getAnalysisById, pollAnalysisUntilDone, startAnalysis } from "@/lib/api";
import { Analysis } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { AlertTriangle, Sparkles } from "lucide-react";
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
      const done = await pollAnalysisUntilDone(queued.job_id, 90, (progress) => {
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

                <AnalysisInput onAnalyze={handleAnalyze} loading={state.kind === "loading"} />

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
        <ActivitySidebar />
      </div>
    </div>
  );
};

export default Analyze;
