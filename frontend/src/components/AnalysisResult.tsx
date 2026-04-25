"use client";

import { Analysis } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { VerdictBadge } from "./VerdictBadge";
import { CredibilityMeter } from "./CredibilityMeter";
import { ClaimCard } from "./ClaimCard";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ThumbsUp, ThumbsDown, MessageSquareWarning, AlertTriangle, HelpCircle, Sparkles } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { castVote } from "@/lib/api";
import { cn } from "@/lib/utils";

export const AnalysisResult = ({ analysis, cached = false }: { analysis: Analysis; cached?: boolean }) => {
  const [localVotes, setLocalVotes] = useState({
    upvotes: analysis.upvotes,
    downvotes: analysis.downvotes,
    myVote: analysis.myVote || "none" as "up" | "down" | "none",
  });
  const [isVoting, setIsVoting] = useState(false);

  const handleVote = async (vote: "up" | "down") => {
    const postId = analysis.postId || analysis.id;
    if (!postId || isVoting) return;
    const oldVote = localVotes.myVote;
    const nextVote = oldVote === vote ? "none" : vote;

    let up = localVotes.upvotes;
    let down = localVotes.downvotes;
    if (oldVote === "up") up -= 1;
    if (oldVote === "down") down -= 1;
    if (nextVote === "up") up += 1;
    if (nextVote === "down") down += 1;
    setLocalVotes({ upvotes: Math.max(0, up), downvotes: Math.max(0, down), myVote: nextVote });

    try {
      setIsVoting(true);
      const result = await castVote(postId, nextVote);
      setLocalVotes({
        upvotes: result.upvotes,
        downvotes: result.downvotes,
        myVote: result.my_vote,
      });
    } catch {
      setLocalVotes({ upvotes: analysis.upvotes, downvotes: analysis.downvotes, myVote: oldVote });
    } finally {
      setIsVoting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {cached && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-primary/10 border border-primary/30 text-sm">
          <Sparkles className="h-4 w-4 text-primary shrink-0" />
          <span><strong className="text-primary">Already analyzed.</strong> Showing cached community analysis from {analysis.submittedAt}.</span>
        </div>
      )}

      {/* Hero verdict card */}
      <Card className="relative overflow-hidden bg-gradient-card border-border/60 shadow-elegant">
        <div className="absolute inset-0 bg-gradient-mesh opacity-10" />
        <div className="relative p-6 md:p-8">
          <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-3">
                <VerdictBadge verdict={analysis.verdict} size="lg" />
                <span className="text-xs font-mono text-muted-foreground">via {analysis.source}</span>
              </div>
              <h2 className="font-serif text-2xl md:text-3xl font-semibold leading-tight text-balance">
                {analysis.title}
              </h2>
            </div>
          </div>

          <p className="text-foreground/80 leading-relaxed mb-6 max-w-3xl">{analysis.summary}</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-2xl">
            <CredibilityMeter score={analysis.overallCredibility} label="Overall Credibility" size="lg" />
            <CredibilityMeter score={analysis.overallConfidence} label="AI Confidence" size="lg" />
          </div>

          <div className="flex items-center gap-2 mt-6 pt-6 border-t border-border/40">
            <Button
              variant="outline"
              size="sm"
              className={cn("gap-1.5", localVotes.myVote === "up" && "text-success border-success/40")}
              onClick={() => void handleVote("up")}
              disabled={isVoting}
            >
              <ThumbsUp className="h-3.5 w-3.5" /> {localVotes.upvotes}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className={cn("gap-1.5", localVotes.myVote === "down" && "text-destructive border-destructive/40")}
              onClick={() => void handleVote("down")}
              disabled={isVoting}
            >
              <ThumbsDown className="h-3.5 w-3.5" /> {localVotes.downvotes}
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5 ml-auto" asChild>
              <Link href={`/analysis/${analysis.id}#dispute`}>
                <MessageSquareWarning className="h-3.5 w-3.5 text-warning" /> Dispute ({analysis.disputes})
              </Link>
            </Button>
          </div>
        </div>
      </Card>

      <Tabs defaultValue="claims" className="w-full">
        <TabsList className="bg-secondary/40">
          <TabsTrigger value="claims">Claims ({analysis.claims.length})</TabsTrigger>
          <TabsTrigger value="reasoning">Reasoning</TabsTrigger>
          <TabsTrigger value="details">False & Uncertain</TabsTrigger>
        </TabsList>

        <TabsContent value="claims" className="space-y-4 mt-4">
          {analysis.claims.length > 0 ? (
            analysis.claims.map((c, i) => <ClaimCard key={c.id} claim={c} index={i} />)
          ) : (
            <Card className="p-8 text-center text-muted-foreground bg-gradient-card">
              No granular claim breakdown available for this analysis yet.
            </Card>
          )}
        </TabsContent>

        <TabsContent value="reasoning" className="mt-4">
          <Card className="p-6 bg-gradient-card">
            <h3 className="font-serif text-xl mb-3">Final Evaluation</h3>
            <p className="text-foreground/85 leading-relaxed">{analysis.reasoning}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {analysis.tags.map((t) => (
                <span key={t} className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground font-mono">
                  #{t}
                </span>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="details" className="mt-4 grid md:grid-cols-2 gap-4">
          <Card className="p-5 bg-destructive/5 border-destructive/30">
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-destructive mb-3">
              <AlertTriangle className="h-4 w-4" /> False Details
            </h3>
            {analysis.falseDetails.length > 0 ? (
              <ul className="space-y-2">
                {analysis.falseDetails.map((d, i) => (
                  <li key={i} className="text-sm flex gap-2"><span className="text-destructive">✕</span>{d}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">None identified.</p>
            )}
          </Card>
          <Card className="p-5 bg-warning/5 border-warning/30">
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-warning mb-3">
              <HelpCircle className="h-4 w-4" /> Uncertain Details
            </h3>
            {analysis.uncertainDetails.length > 0 ? (
              <ul className="space-y-2">
                {analysis.uncertainDetails.map((d, i) => (
                  <li key={i} className="text-sm flex gap-2"><span className="text-warning">?</span>{d}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">None.</p>
            )}
          </Card>
      </TabsContent>
    </Tabs>
  </div>
  );
};
