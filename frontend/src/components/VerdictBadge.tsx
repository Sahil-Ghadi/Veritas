import { cn } from "@/lib/utils";
import { Verdict, verdictMeta } from "@/lib/types";
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle } from "lucide-react";

const iconFor: Record<Verdict, typeof CheckCircle2> = {
  "true": CheckCircle2,
  "mostly-true": CheckCircle2,
  "mixed": AlertTriangle,
  "mostly-false": XCircle,
  "false": XCircle,
  "unverified": HelpCircle,
};

export const VerdictBadge = ({ verdict, size = "sm" }: { verdict: Verdict; size?: "sm" | "md" | "lg" }) => {
  const meta = verdictMeta[verdict];
  const Icon = iconFor[verdict];
  const sizes = {
    sm: "text-xs px-2 py-0.5 gap-1",
    md: "text-sm px-3 py-1 gap-1.5",
    lg: "text-base px-4 py-1.5 gap-2",
  };
  const iconSizes = { sm: "h-3 w-3", md: "h-4 w-4", lg: "h-5 w-5" };
  return (
    <span className={cn("inline-flex items-center whitespace-nowrap font-medium rounded-full ring-1", meta.color, meta.bg, meta.ring, sizes[size])}>
      <Icon className={iconSizes[size]} />
      {meta.label}
    </span>
  );
};
