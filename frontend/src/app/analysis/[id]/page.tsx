"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { AnalysisResult } from "@/components/AnalysisResult";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { mockAnalyses } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { ArrowLeft, MessageSquareWarning, Send, GitCompareArrows, CheckCircle2, ArrowRight } from "lucide-react";
import { VerdictBadge } from "@/components/VerdictBadge";
import { CredibilityMeter } from "@/components/CredibilityMeter";

const AnalysisDetail = () => {
  const params = useParams();
  const id = params?.id as string;
  const analysis = mockAnalyses.find((a) => a.id === id) || mockAnalyses[0];

  const [disputeText, setDisputeText] = useState("");
  const [disputeUrl, setDisputeUrl] = useState("");
  const [phase, setPhase] = useState<"idle" | "running" | "result">("idle");

  const submitDispute = () => {
    if (!disputeText.trim()) return;
    setPhase("running");
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <NavigationSidebar />
      <div className="flex flex-1 min-w-0">
        <main className="flex-1 min-w-0">
          <div className="container max-w-4xl py-8">
            <Button variant="ghost" size="sm" asChild className="mb-4">
              <Link href="/community"><ArrowLeft className="h-4 w-4" /> Back to community</Link>
            </Button>

            <AnalysisResult analysis={analysis} />

            {/* Dispute section */}
            <section id="dispute" className="mt-12 pt-12 border-t border-border/40">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquareWarning className="h-5 w-5 text-warning" />
                <h2 className="font-serif text-2xl md:text-3xl font-semibold">Dispute this analysis</h2>
              </div>
              <p className="text-muted-foreground mb-6 max-w-2xl">
                Found contradictory evidence or think a claim was misjudged? Submit your counter-evidence and we'll re-run the pipeline with your input included.
              </p>

              {phase === "idle" && (
                <Card className="p-6 bg-gradient-card border-warning/30 space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Your counter-claim or correction</label>
                    <Textarea
                      placeholder="Describe what you believe is incorrect and why..."
                      value={disputeText}
                      onChange={(e) => setDisputeText(e.target.value)}
                      className="min-h-[120px] bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Source URL (optional)</label>
                    <Input
                      placeholder="https://..."
                      value={disputeUrl}
                      onChange={(e) => setDisputeUrl(e.target.value)}
                      className="bg-background/50"
                    />
                  </div>
                  <Button
                    onClick={submitDispute}
                    disabled={!disputeText.trim()}
                    className="bg-gradient-accent text-accent-foreground hover:opacity-90 shadow-accent-glow"
                  >
                    <Send className="h-4 w-4" /> Submit & re-run pipeline
                  </Button>
                </Card>
              )}

              {phase === "running" && (
                <div className="space-y-4">
                  <Card className="p-4 bg-warning/5 border-warning/30 text-sm">
                    <div className="flex items-start gap-2">
                      <MessageSquareWarning className="h-4 w-4 text-warning mt-0.5" />
                      <div>
                        <p className="font-medium">Your dispute:</p>
                        <p className="text-muted-foreground italic">"{disputeText}"</p>
                      </div>
                    </div>
                  </Card>
                  <AnalysisProgress onComplete={() => setPhase("result")} />
                </div>
              )}

              {phase === "result" && (
                <DisputeResult original={analysis} disputeText={disputeText} onReset={() => { setPhase("idle"); setDisputeText(""); setDisputeUrl(""); }} />
              )}
            </section>

            {/* Existing disputes */}
            {analysis.disputes > 0 && (
              <section className="mt-12">
                <h3 className="font-serif text-xl font-semibold mb-4">
                  Previous disputes ({analysis.disputes})
                </h3>
                <div className="space-y-3">
                  {Array.from({ length: Math.min(analysis.disputes, 3) }).map((_, i) => (
                    <Card key={i} className="p-4 bg-gradient-card border-border/60">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="h-7 w-7 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-semibold text-primary-foreground">
                            {String.fromCharCode(65 + i)}
                          </div>
                          <span className="text-sm font-medium">user_{i + 1}</span>
                          <span className="text-xs text-muted-foreground font-mono">{i + 1}d ago</span>
                        </div>
                        <VerdictBadge verdict={i === 0 ? "mixed" : "false"} size="sm" />
                      </div>
                      <p className="text-sm text-foreground/80">
                        {i === 0
                          ? "The original study sample size is actually larger; consider including the supplementary cohort data."
                          : i === 1
                            ? "I found another source corroborating part of this claim — should be 'mixed' not 'false'."
                            : "The fabricated quote attribution has since been retracted by the publication."}
                      </p>
                    </Card>
                  ))}
                </div>
              </section>
            )}
          </div>
        </main>
        <ActivitySidebar />
      </div>
    </div>
  );
};

const DisputeResult = ({
  original,
  disputeText,
  onReset,
}: {
  original: typeof mockAnalyses[0];
  disputeText: string;
  onReset: () => void;
}) => {
  // Simulated re-evaluation: nudge credibility, change verdict to mixed
  const newCred = Math.min(100, original.overallCredibility + 18);
  const newConf = Math.max(60, original.overallConfidence - 8);

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="p-6 bg-gradient-card border-primary/30 shadow-glow">
        <div className="flex items-center gap-2 mb-4">
          <GitCompareArrows className="h-5 w-5 text-primary" />
          <h3 className="font-serif text-xl font-semibold">Re-analysis complete</h3>
          <CheckCircle2 className="h-4 w-4 text-success ml-auto" />
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-lg bg-secondary/40 border border-border/40">
            <p className="text-xs uppercase font-mono text-muted-foreground mb-2">Before</p>
            <VerdictBadge verdict={original.verdict} size="md" />
            <div className="mt-3 space-y-2">
              <CredibilityMeter score={original.overallCredibility} label="Credibility" size="sm" />
              <CredibilityMeter score={original.overallConfidence} label="Confidence" size="sm" />
            </div>
          </div>
          <div className="p-4 rounded-lg bg-primary/10 border border-primary/30 relative">
            <ArrowRight className="absolute -left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary bg-background rounded-full p-0.5 hidden md:block" />
            <p className="text-xs uppercase font-mono text-primary mb-2">After dispute</p>
            <VerdictBadge verdict="mixed" size="md" />
            <div className="mt-3 space-y-2">
              <CredibilityMeter score={newCred} label="Credibility" size="sm" />
              <CredibilityMeter score={newConf} label="Confidence" size="sm" />
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-background/50 border border-border/40">
            <p className="text-xs uppercase font-mono text-muted-foreground mb-1">What changed</p>
            <p className="text-sm leading-relaxed">
              Your counter-evidence shifted Claim #3 from <span className="text-warning">mixed</span> toward{" "}
              <span className="text-success">mostly-true</span>, and added uncertainty around the original study's methodology. Overall verdict moved from <span className="text-destructive">false</span> to <span className="text-warning">mixed</span>.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-warning/5 border border-warning/30">
            <p className="text-xs uppercase font-mono text-warning mb-1">New uncertain detail</p>
            <p className="text-sm">Whether the supplementary cohort (n=128) was peer-reviewed alongside the original.</p>
          </div>
        </div>

        <div className="flex gap-2 mt-6 pt-4 border-t border-border/40">
          <Button size="sm" className="bg-gradient-primary text-primary-foreground">Accept update</Button>
          <Button size="sm" variant="outline" onClick={onReset}>Submit another</Button>
        </div>
      </Card>
    </div>
  );
};

export default AnalysisDetail;
