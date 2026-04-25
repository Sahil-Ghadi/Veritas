"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { AnalysisResult } from "@/components/AnalysisResult";
import { getAnalysisById, submitDispute, getDisputesByPostId } from "@/lib/api";
import { auth } from "@/lib/firebase";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, MessageSquareWarning, Send, LogIn, AlertCircle, CheckCircle2, Loader2, History } from "lucide-react";
import { Analysis } from "@/lib/types";
import { cn } from "@/lib/utils";

const AnalysisDetail = () => {
  const params = useParams();
  const id = params?.id as string;
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [disputes, setDisputes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [disputeText, setDisputeText] = useState("");
  const [disputeUrl, setDisputeUrl] = useState("");
  const [claimIndex, setClaimIndex] = useState(0);
  const [phase, setPhase] = useState<"idle" | "running" | "result" | "rejected" | "error">("idle");
  const [disputeMessage, setDisputeMessage] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  // Track auth state
  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      setIsAuthenticated(!!user);
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getAnalysisById(id);
        if (!data) {
          setError("Analysis not found.");
        } else {
          setAnalysis(data);
          const disputesData = await getDisputesByPostId(data.postId || id);
          setDisputes(disputesData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analysis.");
      } finally {
        setLoading(false);
      }
    };
    if (id) void load();
  }, [id]);

  const MIN_ARGUMENT_LENGTH = 20;
  const argumentTooShort = disputeText.trim().length > 0 && disputeText.trim().length < MIN_ARGUMENT_LENGTH;
  const canSubmit = isAuthenticated && disputeText.trim().length >= MIN_ARGUMENT_LENGTH;

  const submitDisputeHandler = async () => {
    if (!canSubmit) return;
    if (!auth.currentUser) {
      setDisputeMessage("You must be signed in to submit a dispute.");
      setPhase("error");
      return;
    }
    setPhase("running");
    setDisputeMessage("");
    try {
      // Use the Firestore post_id (not the job_id in the URL)
      const postId = analysis?.postId || id;
      const response = await submitDispute({
        post_id: postId,
        claim_index: claimIndex,
        dispute_type: "VERDICT",
        counter_argument: disputeText.trim(),
        counter_source_url: disputeUrl.trim() || undefined,
      });
      if (response.status === "VALIDATED") {
        setDisputeMessage(
          `Your dispute was validated! New credibility score: ${Math.round((response.new_score || 0) * 100)}%.`
        );
      } else {
        setDisputeMessage(
          response.reason || "Your dispute was reviewed but could not be validated at this time."
        );
      }
      setPhase(response.status === "VALIDATED" ? "result" : "rejected");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to submit dispute.";
      setDisputeMessage(msg);
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
                Found contradictory evidence or think a claim was misjudged? Submit your counter-evidence and our pipeline will re-evaluate it with your input.
              </p>

              {/* Not signed in */}
              {isAuthenticated === false && (
                <Card className="p-6 border-border/50 bg-muted/20 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                  <LogIn className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="flex-1">
                    <p className="font-semibold">Sign in to submit a dispute</p>
                    <p className="text-sm text-muted-foreground mt-0.5">You must have a verified account to challenge an analysis result.</p>
                  </div>
                  <Button asChild size="sm">
                    <Link href="/auth">Sign in</Link>
                  </Button>
                </Card>
              )}

              {/* Idle form — show only when authenticated */}
              {isAuthenticated && phase === "idle" && (
                <Card className="p-6 bg-gradient-card border-warning/30 space-y-5">
                  {/* Claim selector (only shown if there are multiple claims) */}
                  {analysis.claims.length > 1 && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Which claim are you disputing?</label>
                      <Select
                        value={String(claimIndex)}
                        onValueChange={(v) => setClaimIndex(Number(v))}
                      >
                        <SelectTrigger className="bg-background/50 h-auto min-h-[2.5rem] py-3 text-left [&>span]:line-clamp-none [&>span]:whitespace-normal [&>span]:break-words [&>span]:w-full">
                          <SelectValue placeholder="Select a claim" />
                        </SelectTrigger>
                        <SelectContent className="max-h-[300px] w-[var(--radix-select-trigger-width)]">
                          {analysis.claims.map((claim, i) => (
                            <SelectItem key={i} value={String(i)} className="whitespace-normal py-3">
                              <span className="flex items-start text-left">
                                <span className="text-xs font-mono text-muted-foreground mr-3 mt-0.5 shrink-0">#{i + 1}</span>
                                <span className="leading-tight">{claim.text}</span>
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">Your counter-claim or correction</label>
                    <Textarea
                      placeholder="Describe what you believe is incorrect and why... (minimum 20 characters)"
                      value={disputeText}
                      onChange={(e) => setDisputeText(e.target.value)}
                      className={cn(
                        "min-h-[120px] bg-background/50 transition-colors",
                        argumentTooShort && "border-destructive/60 focus-visible:ring-destructive/30"
                      )}
                    />
                    <div className="flex items-center justify-between">
                      {argumentTooShort ? (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          At least {MIN_ARGUMENT_LENGTH} characters required ({disputeText.trim().length}/{MIN_ARGUMENT_LENGTH})
                        </p>
                      ) : (
                        <span />
                      )}
                      <span className={cn(
                        "text-xs font-mono text-muted-foreground",
                        disputeText.trim().length >= MIN_ARGUMENT_LENGTH && "text-success"
                      )}>
                        {disputeText.trim().length} chars
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">Source URL <span className="text-muted-foreground font-normal">(optional but recommended)</span></label>
                    <Input
                      placeholder="https://..."
                      value={disputeUrl}
                      onChange={(e) => setDisputeUrl(e.target.value)}
                      className="bg-background/50"
                    />
                    <p className="text-xs text-muted-foreground">A credible source URL significantly improves your dispute's chances of being validated.</p>
                  </div>

                  <Button
                    onClick={submitDisputeHandler}
                    disabled={!canSubmit}
                    className="bg-gradient-accent text-accent-foreground hover:opacity-90 shadow-accent-glow"
                  >
                    <Send className="h-4 w-4" /> Submit &amp; re-evaluate
                  </Button>
                </Card>
              )}

              {/* Running */}
              {phase === "running" && (
                <Card className="p-6 bg-warning/5 border-warning/30">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 text-warning animate-spin" />
                    <div>
                      <p className="font-semibold">Evaluating your dispute...</p>
                      <p className="text-sm text-muted-foreground mt-0.5">Our pipeline is reviewing your counter-evidence. This may take a moment.</p>
                    </div>
                  </div>
                </Card>
              )}

              {/* Validated */}
              {phase === "result" && (
                <Card className="p-6 bg-success/5 border-success/30">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-success mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <p className="font-semibold text-success">Dispute validated</p>
                      <p className="text-sm text-muted-foreground mt-1">{disputeMessage}</p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-4"
                        onClick={() => { setPhase("idle"); setDisputeText(""); setDisputeUrl(""); }}
                      >
                        Submit another dispute
                      </Button>
                    </div>
                  </div>
                </Card>
              )}

              {/* Rejected (valid submission, not accepted by AI) */}
              {phase === "rejected" && (
                <Card className="p-6 bg-warning/5 border-warning/30">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-warning mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <p className="font-semibold text-warning">Dispute not validated</p>
                      <p className="text-sm text-muted-foreground mt-1">{disputeMessage}</p>
                      <p className="text-xs text-muted-foreground mt-2">Try providing a more specific argument or a credible source URL to strengthen your case.</p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-4"
                        onClick={() => { setPhase("idle"); setDisputeText(""); setDisputeUrl(""); }}
                      >
                        Try again with more evidence
                      </Button>
                    </div>
                  </div>
                </Card>
              )}

              {/* Error */}
              {phase === "error" && (
                <Card className="p-6 bg-destructive/5 border-destructive/30">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-destructive mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <p className="font-semibold text-destructive">Submission failed</p>
                      <p className="text-sm text-muted-foreground mt-1">{disputeMessage}</p>
                      <Button size="sm" variant="outline" className="mt-4" onClick={() => setPhase("idle")}>
                        Try again
                      </Button>
                    </div>
                  </div>
                </Card>
              )}
            </section>

            {disputes.length > 0 && (
              <section className="mt-12 pt-12 border-t border-border/40">
                <div className="flex items-center gap-2 mb-6">
                  <History className="h-5 w-5 text-muted-foreground" />
                  <h2 className="font-serif text-2xl font-semibold">Dispute History</h2>
                </div>
                <div className="space-y-4">
                  {disputes.map((d, i) => (
                    <Card key={d.id || i} className="p-5 bg-background border-border/40">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "text-xs font-semibold px-2 py-0.5 rounded-full uppercase",
                            d.status === "VALIDATED" ? "bg-success/20 text-success" :
                            d.status === "REJECTED" ? "bg-warning/20 text-warning" :
                            "bg-muted text-muted-foreground"
                          )}>
                            {d.status}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(d.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {d.score_impact !== undefined && d.score_impact !== null && (
                          <span className={cn(
                            "text-sm font-bold",
                            d.score_impact > 0 ? "text-success" : d.score_impact < 0 ? "text-destructive" : "text-muted-foreground"
                          )}>
                            {d.score_impact > 0 ? "+" : ""}{d.score_impact} credibility
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium mt-3 mb-1">Counter-argument:</p>
                      <p className="text-sm text-muted-foreground bg-muted/30 p-3 rounded-md italic">
                        "{d.counter_argument}"
                      </p>
                      
                      {d.validation_result?.reason && (
                        <div className="mt-4 pt-3 border-t border-border/30">
                          <p className="text-sm font-medium mb-1">AI Verdict:</p>
                          <p className="text-sm text-muted-foreground">
                            {d.validation_result.reason}
                          </p>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </section>
            )}

          </div>
        </main>
        <ActivitySidebar analysis={analysis ?? undefined} />
      </div>
    </div>
  );
};

export default AnalysisDetail;
