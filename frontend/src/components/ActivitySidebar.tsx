"use client";

import { useEffect, useState } from "react";
import { buildRecentActivity, getAllAnalyses } from "@/lib/api";
import { ActivityItem } from "@/lib/types";
import { VerdictBadge } from "./VerdictBadge";
import { Activity, MessageSquareWarning, FileSearch, ChevronRight, Search } from "lucide-react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export const ActivitySidebar = () => {
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const analyses = await getAllAnalyses();
        setRecentActivity(buildRecentActivity(analyses));
      } catch {
        setRecentActivity([]);
      }
    };
    void load();
  }, []);

  return (
    <aside className="hidden lg:flex flex-col w-72 shrink-0 border-l border-border/40 bg-sidebar/40 h-screen sticky top-0">
      <div className="p-4 border-b border-border/40">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Recent Activity</h3>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input placeholder="Search history..." className="h-9 pl-9 text-sm bg-background/50" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {recentActivity.map((item, idx) => (
          <Link
            key={item.id}
            href={`/analysis/${item.id}`}
            className="group block p-3 rounded-lg hover:bg-sidebar-accent transition-all duration-300 ease-smooth animate-fade-in border border-transparent hover:border-border/60"
            style={{ animationDelay: `${idx * 40}ms` }}
          >
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 p-1.5 rounded-md bg-secondary group-hover:bg-primary/10 transition-colors">
                {item.type === "dispute" ? (
                  <MessageSquareWarning className="h-3.5 w-3.5 text-warning" />
                ) : (
                  <FileSearch className="h-3.5 w-3.5 text-primary" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium leading-snug truncate">{item.title}</p>
                <div className="flex items-center justify-between mt-1.5">
                  <VerdictBadge verdict={item.verdict} size="sm" />
                  <span className="text-[10px] font-mono text-muted-foreground">{item.time}</span>
                </div>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition-all" />
            </div>
          </Link>
        ))}
      </div>

      <div className="p-3 border-t border-border/40">
        <Button variant="outline" size="sm" className="w-full" asChild>
          <Link href="/community">View all activity</Link>
        </Button>
      </div>
    </aside>
  );
};
