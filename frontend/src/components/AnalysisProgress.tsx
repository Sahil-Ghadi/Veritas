import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, Search, Sparkles, ScanLine, Scale } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  { id: 1, label: "Extracting content", icon: ScanLine },
  { id: 2, label: "Identifying claims", icon: Search },
  { id: 3, label: "Cross-referencing sources", icon: Sparkles },
  { id: 4, label: "Scoring credibility", icon: Scale },
  { id: 5, label: "Generating verdict", icon: CheckCircle2 },
];

export const AnalysisProgress = ({ onComplete }: { onComplete: () => void }) => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step >= STEPS.length) {
      const t = setTimeout(onComplete, 400);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setStep(step + 1), 700);
    return () => clearTimeout(t);
  }, [step, onComplete]);

  return (
    <div className="bg-gradient-card border border-border/60 rounded-2xl p-8 shadow-elegant animate-scale-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/30 blur-xl animate-pulse" />
          <Loader2 className="relative h-5 w-5 text-primary animate-spin" />
        </div>
        <h3 className="font-serif text-xl">Running analysis pipeline</h3>
      </div>

      <div className="space-y-3">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const done = i < step;
          const active = i === step;
          return (
            <div
              key={s.id}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg transition-all duration-500",
                active && "bg-primary/10 border border-primary/30",
                done && "opacity-60"
              )}
            >
              <div
                className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center transition-all duration-500",
                  done && "bg-success/20 text-success",
                  active && "bg-primary/20 text-primary animate-pulse-glow",
                  !done && !active && "bg-secondary text-muted-foreground"
                )}
              >
                {done ? <CheckCircle2 className="h-4 w-4" /> : <Icon className={cn("h-4 w-4", active && "animate-pulse")} />}
              </div>
              <span className={cn("text-sm font-medium flex-1", active && "text-foreground", !active && !done && "text-muted-foreground")}>
                {s.label}
              </span>
              {active && (
                <span className="text-xs font-mono text-primary animate-pulse">processing...</span>
              )}
              {done && <span className="text-xs font-mono text-success">done</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
};
