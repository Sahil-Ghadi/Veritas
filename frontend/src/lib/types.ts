export type Verdict = "true" | "mostly-true" | "mixed" | "mostly-false" | "false" | "unverified";

export interface Evidence {
  id: string;
  source: string;
  url: string;
  title: string;
  stance: "supports" | "contradicts" | "context";
  excerpt: string;
  credibility: number;
}

export interface Claim {
  id: string;
  text: string;
  verdict: Verdict;
  confidence: number;
  credibilityScore: number;
  reasoning: string;
  supporting: Evidence[];
  contradicting: Evidence[];
  uncertainDetails?: string[];
}

export interface Analysis {
  id: string;
  title: string;
  source: string;
  inputType: "url" | "text" | "image";
  inputPreview: string;
  submittedBy: string;
  submittedAt: string;
  verdict: Verdict;
  overallCredibility: number;
  overallConfidence: number;
  summary: string;
  reasoning: string;
  falseDetails: string[];
  uncertainDetails: string[];
  claims: Claim[];
  upvotes: number;
  downvotes: number;
  disputes: number;
  tags: string[];
}

export interface ActivityItem {
  id: string;
  type: "analysis" | "dispute";
  title: string;
  verdict: Verdict;
  time: string;
}

export const verdictMeta: Record<Verdict, { label: string; color: string; bg: string; ring: string }> = {
  "true": { label: "Verified True", color: "text-success", bg: "bg-success/10", ring: "ring-success/30" },
  "mostly-true": { label: "Mostly True", color: "text-success", bg: "bg-success/10", ring: "ring-success/30" },
  "mixed": { label: "Mixed Evidence", color: "text-warning", bg: "bg-warning/10", ring: "ring-warning/30" },
  "mostly-false": { label: "Mostly False", color: "text-destructive", bg: "bg-destructive/10", ring: "ring-destructive/30" },
  "false": { label: "False", color: "text-destructive", bg: "bg-destructive/10", ring: "ring-destructive/30" },
  "unverified": { label: "Unverified", color: "text-muted-foreground", bg: "bg-muted/40", ring: "ring-border" },
};
