import { cn } from "@/lib/utils";

interface CredibilityMeterProps {
  score: number; // 0-100
  size?: "sm" | "md" | "lg";
  label?: string;
  showValue?: boolean;
}

export const CredibilityMeter = ({ score, size = "md", label, showValue = true }: CredibilityMeterProps) => {
  const color =
    score >= 75 ? "bg-success" : score >= 50 ? "bg-warning" : score >= 25 ? "bg-accent" : "bg-destructive";
  const textColor =
    score >= 75 ? "text-success" : score >= 50 ? "text-warning" : score >= 25 ? "text-accent" : "text-destructive";
  const heights = { sm: "h-1", md: "h-2", lg: "h-3" };

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && <span className="text-xs text-muted-foreground">{label}</span>}
          {showValue && <span className={cn("text-xs font-mono font-semibold", textColor)}>{score}%</span>}
        </div>
      )}
      <div className={cn("w-full bg-secondary rounded-full overflow-hidden", heights[size])}>
        <div
          className={cn("h-full rounded-full transition-all duration-1000 ease-smooth relative", color)}
          style={{ width: `${score}%` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer bg-[length:200%_100%]" />
        </div>
      </div>
    </div>
  );
};
