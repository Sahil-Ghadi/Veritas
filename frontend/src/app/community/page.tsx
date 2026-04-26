"use client";

import Link from "next/link";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VerdictBadge } from "@/components/VerdictBadge";
import { CredibilityMeter } from "@/components/CredibilityMeter";
import { castVote, getAllAnalyses } from "@/lib/api";
import { ThumbsUp, ThumbsDown, MessageSquareWarning, TrendingUp, Clock, Flame, Search, Link2, FileText, Image as ImageIcon, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Analysis } from "@/lib/types";

const filters = [
  { id: "trending", label: "Trending", icon: Flame },
  { id: "recent", label: "Recent", icon: Clock },
  { id: "disputed", label: "Disputed", icon: MessageSquareWarning },
  { id: "top", label: "Top Voted", icon: TrendingUp },
];

const Community = () => {
  const [active, setActive] = useState("trending");
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [votingIds, setVotingIds] = useState<Record<string, boolean>>({});
  const [searchQuery, setSearchQuery] = useState("");

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const data = await getAllAnalyses();
        setAnalyses(data);
      } catch {
        setAnalyses([]);
      } finally {
        setIsLoading(false);
      }
    };
    void load();
  }, []);

  const visibleAnalyses = useMemo(() => {
    let sorted: Analysis[];
    if (active === "recent") sorted = analyses;
    else if (active === "disputed") sorted = analyses.filter((a) => (a.disputes || 0) > 0);
    else if (active === "top") sorted = [...analyses].sort((a, b) => (b.upvotes - b.downvotes) - (a.upvotes - a.downvotes));
    else {
      // For 'trending', sort by total engagement (votes + disputes)
      sorted = [...analyses].sort((a, b) => {
        const engA = (a.upvotes || 0) + (a.downvotes || 0) + (a.disputes || 0) * 2;
        const engB = (b.upvotes || 0) + (b.downvotes || 0) + (b.disputes || 0) * 2;
        return engB - engA;
      });
    }

    if (!searchQuery.trim()) return sorted;
    const q = searchQuery.toLowerCase();
    return sorted.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.summary.toLowerCase().includes(q) ||
        a.tags.some((t) => t.toLowerCase().includes(q)) ||
        a.submittedBy.toLowerCase().includes(q)
    );
  }, [active, analyses, searchQuery]);

  const handleVote = async (postId: string | undefined, vote: "up" | "down") => {
    if (!postId) return;
    if (votingIds[postId]) return;
    const target = analyses.find((a) => (a.postId || a.id) === postId);
    if (!target) return;

    const oldVote = target.myVote || "none";
    const nextVote = oldVote === vote ? "none" : vote;

    setVotingIds((prev) => ({ ...prev, [postId]: true }));
    setAnalyses((prev) =>
      prev.map((a) => {
        if ((a.postId || a.id) !== postId) return a;
        let up = a.upvotes;
        let down = a.downvotes;
        if (oldVote === "up") up -= 1;
        if (oldVote === "down") down -= 1;
        if (nextVote === "up") up += 1;
        if (nextVote === "down") down += 1;
        return { ...a, upvotes: Math.max(0, up), downvotes: Math.max(0, down), myVote: nextVote };
      })
    );

    try {
      const result = await castVote(postId, nextVote);
      setAnalyses((prev) =>
        prev.map((a) =>
          (a.postId || a.id) === postId
            ? {
                ...a,
                upvotes: result.upvotes,
                downvotes: result.downvotes,
                myVote: result.my_vote,
              }
            : a
        )
      );
    } catch {
      try {
        const refreshed = await getAllAnalyses();
        setAnalyses(refreshed);
      } catch {
        setAnalyses((prev) =>
          prev.map((a) => ((a.postId || a.id) === postId ? { ...a, myVote: oldVote } : a))
        );
      }
    } finally {
      setVotingIds((prev) => ({ ...prev, [postId]: false }));
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <NavigationSidebar />

      <div className="flex flex-1 min-w-0">
        <main className="flex-1 min-w-0">
          <div className="container max-w-5xl py-8 md:py-12">
            <div className="mb-8 animate-fade-in-up">
              <p className="text-xs font-mono uppercase tracking-widest text-accent mb-2">Community</p>
              <h1 className="font-display text-4xl md:text-5xl italic font-light tracking-tightest">
                Let the crowd verify claim. <span className="italic font-light"></span>
              </h1>
              <p className="text-muted-foreground mt-3 max-w-3xl text-lg">
                Every analysis Veritas runs is shared here. Vote, dispute, or contribute counter-evidence.
              </p>
            </div>

            <div className="flex flex-col md:flex-row gap-3 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search analyses, claims, sources..."
                  className="h-11 pl-10 bg-gradient-card border-border/60"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchQuery.trim() && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-muted-foreground">
                    {visibleAnalyses.length} result{visibleAnalyses.length !== 1 ? "s" : ""}
                  </span>
                )}
              </div>
              <div className="flex gap-1 p-1 bg-secondary/40 rounded-xl">
                {filters.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setActive(f.id)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-300",
                      active === f.id ? "bg-background text-foreground shadow-card" : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <f.icon className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">{f.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-24 text-muted-foreground animate-pulse">
                  <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
                  <p>Loading community analyses...</p>
                </div>
              ) : visibleAnalyses.length > 0 ? (
                visibleAnalyses.map((a, i) => (
                  <Link
                    key={a.postId || a.id}
                    href={`/analysis/${a.postId || a.id}`}
                    className="block group animate-fade-in-up"
                    style={{ animationDelay: `${i * 60}ms` }}
                  >
                    <Card className="p-5 md:p-6 bg-gradient-card border-border/60 hover:border-primary/40 transition-all duration-500 ease-smooth hover:-translate-y-0.5 hover:shadow-elegant">
                      <div className="flex flex-col md:flex-row gap-5">
                        {/* Vote column */}
                        <div className="flex md:flex-col items-center gap-2 md:w-16 shrink-0">
                          <button
                            className={cn(
                              "p-1.5 rounded hover:bg-success/10 hover:text-success transition-colors",
                              a.myVote === "up" && "text-success bg-success/10"
                            )}
                            onClick={(e) => {
                              e.preventDefault();
                              void handleVote(a.postId, "up");
                            }}
                            disabled={Boolean(votingIds[a.postId || a.id])}
                          >
                            <ThumbsUp className="h-4 w-4" />
                          </button>
                          <span className="font-mono text-sm font-semibold">
                            {(a.upvotes - a.downvotes).toLocaleString()}
                          </span>
                          <button
                            className={cn(
                              "p-1.5 rounded hover:bg-destructive/10 hover:text-destructive transition-colors",
                              a.myVote === "down" && "text-destructive bg-destructive/10"
                            )}
                            onClick={(e) => {
                              e.preventDefault();
                              void handleVote(a.postId, "down");
                            }}
                            disabled={Boolean(votingIds[a.postId || a.id])}
                          >
                            <ThumbsDown className="h-4 w-4" />
                          </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <VerdictBadge verdict={a.verdict} size="sm" />
                            <InputTypeBadge type={a.inputType} />
                            <span className="text-xs font-mono text-muted-foreground">via {a.source}</span>
                          </div>

                          <h3 className="font-serif text-xl md:text-2xl font-semibold leading-tight text-balance group-hover:text-primary transition-colors">
                            {a.title}
                          </h3>

                          <p className="text-sm text-muted-foreground mt-2 leading-relaxed line-clamp-2">{a.summary}</p>

                          <div className="grid sm:grid-cols-2 gap-4 mt-4 max-w-md">
                            <CredibilityMeter score={a.overallCredibility} label="Credibility" size="sm" />
                            <CredibilityMeter score={a.overallConfidence} label="Confidence" size="sm" />
                          </div>

                          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border/40 text-xs text-muted-foreground font-mono">
                            <span>@{a.submittedBy}</span>
                            <span>·</span>
                            <span>{a.submittedAt}</span>
                            <span>·</span>
                            <span className="flex items-center gap-1">
                              <MessageSquareWarning className="h-3 w-3 text-warning" />
                              {a.disputes} disputes
                            </span>
                            {a.tags.slice(0, 2).map((t) => (
                              <span key={t} className="hidden md:inline px-2 py-0.5 rounded-full bg-secondary">#{t}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))
              ) : (
                <Card className="p-6 text-sm text-muted-foreground bg-gradient-card border-border/60 text-center">
                  {searchQuery.trim()
                    ? `No analyses match "${searchQuery}". Try a different search term.`
                    : "No analyses available yet. Run an analysis from the analyze page and it will appear here."}
                </Card>
              )}
            </div>

            <div className="mt-8 text-center">
              <Button variant="outline">Load more</Button>
            </div>
          </div>
        </main>
        <ActivitySidebar />
      </div>
    </div>
  );
};

const InputTypeBadge = ({ type }: { type: "url" | "text" | "image" }) => {
  const Icon = type === "url" ? Link2 : type === "text" ? FileText : ImageIcon;
  return (
    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground font-mono">
      <Icon className="h-3 w-3" />
      {type}
    </span>
  );
};

export default Community;
