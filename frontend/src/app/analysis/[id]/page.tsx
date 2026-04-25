"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { AnalysisResult } from "@/components/AnalysisResult";
import { getAnalysisById, submitDispute } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { ArrowLeft, MessageSquareWarning, Send } from "lucide-react";
import { Analysis } from "@/lib/types";

const AnalysisDetail = () => {
  const params = useParams();
  const id = params?.id as string;
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [disputeText, setDisputeText] = useState("");
  const [disputeUrl, setDisputeUrl] = useState("");
  const [phase, setPhase] = useState<"idle" | "running" | "result" | "error">("idle");
  const [disputeMessage, setDisputeMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getAnalysisById(id);
        if (!data) {
          setError("Analysis not found.");
        } else {
          setAnalysis(data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analysis.");
      } finally {
        setLoading(false);
      }
    };
    if (id) void load();
  }, [id]);

  const submitDisputeHandler = async () => {
    if (!disputeText.trim()) return;
    setPhase("running");
    setDisputeMessage("");
    try {
      const response = await submitDispute({
        post_id: id,
        claim_index: 0,
        dispute_type: "VERDICT",
        counter_argument: disputeText.trim(),
        counter_source_url: disputeUrl.trim() || undefined,
      });
      setDisputeMessage(
        response.status === "VALIDATED"
          ? `Dispute validated. New score: ${Math.round((response.new_score || 0) * 100)}%`
          : response.reason || "Dispute submitted."
      );
      setPhase("result");
    } catch (err) {
      setDisputeMessage(err instanceof Error ? err.message : "Failed to submit dispute.");
      setPhase("error");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-muted-foreground">
        Loading analysis...
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="p-6 max-w-lg text-center">
          <p className="font-semibold">Unable to load analysis</p>
          <p className="text-sm text-muted-foreground mt-2">{error || "Unknown error"}</p>
          <Button asChild className="mt-4">
            <Link href="/community">Back to community</Link>
          </Button>
        </Card>
      </div>
    );
  }

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
                    onClick={submitDisputeHandler}
                    disabled={!disputeText.trim()}
                    className="bg-gradient-accent text-accent-foreground hover:opacity-90 shadow-accent-glow"
                  >
                    <Send className="h-4 w-4" /> Submit & re-run pipeline
                  </Button>
                </Card>
              )}

              {phase === "running" && (
                <Card className="p-4 bg-warning/5 border-warning/30 text-sm">
                  <p className="font-medium">Submitting dispute...</p>
                </Card>
              )}

              {phase === "result" && (
                <Card className="p-6 bg-success/5 border-success/30">
                  <p className="font-semibold text-success">Dispute submitted</p>
                  <p className="text-sm text-muted-foreground mt-2">{disputeMessage}</p>
                  <Button size="sm" variant="outline" className="mt-4" onClick={() => { setPhase("idle"); setDisputeText(""); setDisputeUrl(""); }}>
                    Submit another
                  </Button>
                </Card>
              )}

              {phase === "error" && (
                <Card className="p-6 bg-destructive/5 border-destructive/30">
                  <p className="font-semibold text-destructive">Dispute failed</p>
                  <p className="text-sm text-muted-foreground mt-2">{disputeMessage}</p>
                  <Button size="sm" variant="outline" className="mt-4" onClick={() => setPhase("idle")}>
                    Try again
                  </Button>
                </Card>
              )}
            </section>

          </div>
        </main>
        <ActivitySidebar />
      </div>
    </div>
  );
};

export default AnalysisDetail;
