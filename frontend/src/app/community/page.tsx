"use client";

import Link from "next/link";
import { NavigationSidebar } from "@/components/NavigationSidebar";
import { ActivitySidebar } from "@/components/ActivitySidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VerdictBadge } from "@/components/VerdictBadge";
import { CredibilityMeter } from "@/components/CredibilityMeter";
import { mockAnalyses } from "@/lib/mockData";
import { ThumbsUp, ThumbsDown, MessageSquareWarning, TrendingUp, Clock, Flame, Search, Link2, FileText, Image as ImageIcon } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const filters = [
  { id: "trending", label: "Trending", icon: Flame },
  { id: "recent", label: "Recent", icon: Clock },
  { id: "disputed", label: "Disputed", icon: MessageSquareWarning },
  { id: "top", label: "Top Voted", icon: TrendingUp },
];

const Community = () => {
  const [active, setActive] = useState("trending");

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <NavigationSidebar />

      <div className="flex flex-1 min-w-0">
        <main className="flex-1 min-w-0">
          <div className="container max-w-5xl py-8 md:py-12">
            <div className="mb-8 animate-fade-in-up">
              <p className="text-xs font-mono uppercase tracking-widest text-accent mb-2">— Community</p>
              <h1 className="font-display text-4xl md:text-5xl font-medium tracking-tightest">
                Verified <span className="italic font-light">by the crowd.</span>
              </h1>
              <p className="text-muted-foreground mt-3 max-w-2xl text-lg">
                Every analysis Veritas runs is shared here. Vote, dispute, or contribute counter-evidence.
              </p>
            </div>

            <div className="flex flex-col md:flex-row gap-3 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search analyses, claims, sources..." className="h-11 pl-10 bg-gradient-card border-border/60" />
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
              {mockAnalyses.map((a, i) => (
                <Link
                  key={a.id}
                  href={`/analysis/${a.id}`}
                  className="block group animate-fade-in-up"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <Card className="p-5 md:p-6 bg-gradient-card border-border/60 hover:border-primary/40 transition-all duration-500 ease-smooth hover:-translate-y-0.5 hover:shadow-elegant">
                    <div className="flex flex-col md:flex-row gap-5">
                      {/* Vote column */}
                      <div className="flex md:flex-col items-center gap-2 md:w-16 shrink-0">
                        <button
                          className="p-1.5 rounded hover:bg-success/10 hover:text-success transition-colors"
                          onClick={(e) => e.preventDefault()}
                        >
                          <ThumbsUp className="h-4 w-4" />
                        </button>
                        <span className="font-mono text-sm font-semibold">
                          {(a.upvotes - a.downvotes).toLocaleString()}
                        </span>
                        <button
                          className="p-1.5 rounded hover:bg-destructive/10 hover:text-destructive transition-colors"
                          onClick={(e) => e.preventDefault()}
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
              ))}
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
