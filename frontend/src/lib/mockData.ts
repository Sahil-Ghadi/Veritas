export type Verdict = "true" | "mostly-true" | "mixed" | "mostly-false" | "false" | "unverified";

export interface Evidence {
  id: string;
  source: string;
  url: string;
  title: string;
  stance: "supports" | "contradicts" | "context";
  excerpt: string;
  credibility: number; // 0-100
}

export interface Claim {
  id: string;
  text: string;
  verdict: Verdict;
  confidence: number; // 0-100
  credibilityScore: number; // 0-100
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

export const verdictMeta: Record<Verdict, { label: string; color: string; bg: string; ring: string }> = {
  "true": { label: "Verified True", color: "text-success", bg: "bg-success/10", ring: "ring-success/30" },
  "mostly-true": { label: "Mostly True", color: "text-success", bg: "bg-success/10", ring: "ring-success/30" },
  "mixed": { label: "Mixed Evidence", color: "text-warning", bg: "bg-warning/10", ring: "ring-warning/30" },
  "mostly-false": { label: "Mostly False", color: "text-destructive", bg: "bg-destructive/10", ring: "ring-destructive/30" },
  "false": { label: "False", color: "text-destructive", bg: "bg-destructive/10", ring: "ring-destructive/30" },
  "unverified": { label: "Unverified", color: "text-muted-foreground", bg: "bg-muted/40", ring: "ring-border" },
};

export const mockAnalyses: Analysis[] = [
  {
    id: "a1",
    title: "Scientists confirm coffee reverses aging in new 2024 study",
    source: "healthbuzznews.co",
    inputType: "url",
    inputPreview: "https://healthbuzznews.co/coffee-reverses-aging-study-2024",
    submittedBy: "anna.k",
    submittedAt: "2h ago",
    verdict: "false",
    overallCredibility: 18,
    overallConfidence: 92,
    summary:
      "The article misrepresents a small observational study. No peer-reviewed evidence supports the claim that coffee reverses biological aging.",
    reasoning:
      "The cited study was not peer-reviewed and observed a weak correlation between coffee intake and reduced inflammation in 42 participants. The article extrapolates this into causal anti-aging claims unsupported by the underlying research. Two of the three quoted experts have publicly disputed the framing.",
    falseDetails: [
      "Headline claim 'reverses aging' — not supported by the cited study",
      "Quote attributed to Dr. Helena Voss is fabricated; she issued a public denial",
      "'Confirmed by Harvard researchers' — no Harvard affiliation found",
    ],
    uncertainDetails: [
      "The actual sample size of the original preprint",
      "Whether observed inflammation markers persist beyond 8 weeks",
    ],
    tags: ["health", "misinformation", "study-misrepresentation"],
    upvotes: 342,
    downvotes: 12,
    disputes: 4,
    claims: [
      {
        id: "c1",
        text: "Drinking 3 cups of coffee daily reverses biological aging.",
        verdict: "false",
        confidence: 94,
        credibilityScore: 8,
        reasoning:
          "No peer-reviewed study demonstrates causal aging reversal from coffee consumption. The cited preprint shows only modest anti-inflammatory correlation.",
        supporting: [],
        contradicting: [
          {
            id: "e1",
            source: "Nature Aging",
            url: "#",
            title: "Coffee consumption and biological age: a meta-analysis",
            stance: "contradicts",
            excerpt: "No causal link between coffee intake and reversal of epigenetic aging markers was found across 14 cohorts.",
            credibility: 96,
          },
          {
            id: "e2",
            source: "Reuters Fact Check",
            url: "#",
            title: "Viral coffee 'aging cure' study misrepresented",
            stance: "contradicts",
            excerpt: "Original authors confirmed the article overstates findings and misattributes quotes.",
            credibility: 92,
          },
        ],
        uncertainDetails: ["Long-term effects beyond 8 weeks remain unstudied"],
      },
      {
        id: "c2",
        text: "Harvard researchers led the study.",
        verdict: "false",
        confidence: 99,
        credibilityScore: 4,
        reasoning: "No Harvard-affiliated author appears on the original preprint. The lead author is from a private research lab.",
        supporting: [],
        contradicting: [
          {
            id: "e3",
            source: "Harvard Gazette",
            url: "#",
            title: "Statement on viral coffee study attribution",
            stance: "contradicts",
            excerpt: "Harvard University has no involvement with the referenced research.",
            credibility: 98,
          },
        ],
      },
      {
        id: "c3",
        text: "Coffee reduces inflammation markers in adults.",
        verdict: "mostly-true",
        confidence: 78,
        credibilityScore: 72,
        reasoning: "Multiple peer-reviewed studies show modest reductions in CRP and IL-6 markers among regular coffee drinkers.",
        supporting: [
          {
            id: "e4",
            source: "American Journal of Clinical Nutrition",
            url: "#",
            title: "Coffee, inflammation and cardiovascular markers",
            stance: "supports",
            excerpt: "Habitual coffee intake correlates with lower systemic inflammation in healthy adults.",
            credibility: 88,
          },
        ],
        contradicting: [],
      },
    ],
  },
  {
    id: "a2",
    title: "EU passes landmark AI safety law requiring red-team audits",
    source: "reuters.com",
    inputType: "url",
    inputPreview: "https://reuters.com/eu-ai-act-update-2025",
    submittedBy: "marco.dev",
    submittedAt: "5h ago",
    verdict: "mostly-true",
    overallCredibility: 86,
    overallConfidence: 88,
    summary: "The EU AI Act provisions are accurately described, though the enforcement timeline in the article is slightly overstated.",
    reasoning: "Cross-referenced against official EU Commission documents and three major newswires. Core claims hold; one timeline detail is off by 6 months.",
    falseDetails: ["'Effective immediately' framing — actual enforcement begins in phases starting 2026"],
    uncertainDetails: ["Exact penalty calculation methodology"],
    tags: ["politics", "tech", "regulation"],
    upvotes: 189,
    downvotes: 6,
    disputes: 1,
    claims: [],
  },
  {
    id: "a3",
    title: "Photo shows astronaut planting flag on Mars",
    source: "social-media",
    inputType: "image",
    inputPreview: "mars_flag.jpg",
    submittedBy: "skeptic42",
    submittedAt: "1d ago",
    verdict: "false",
    overallCredibility: 6,
    overallConfidence: 99,
    summary: "Image is AI-generated. No crewed mission to Mars has occurred.",
    reasoning: "Reverse image search and metadata analysis show the image was generated by a diffusion model in 2024. No space agency has conducted a crewed Mars landing.",
    falseDetails: ["Image is AI-generated", "No crewed Mars mission exists to date"],
    uncertainDetails: [],
    tags: ["space", "deepfake", "image-forensics"],
    upvotes: 521,
    downvotes: 3,
    disputes: 0,
    claims: [],
  },
  {
    id: "a4",
    title: "City council approves 24/7 public transit pilot",
    source: "localnews.org",
    inputType: "text",
    inputPreview: "The city council voted 7-2 to approve a pilot program for round-the-clock bus service starting next month...",
    submittedBy: "transit_fan",
    submittedAt: "3d ago",
    verdict: "true",
    overallCredibility: 94,
    overallConfidence: 91,
    summary: "Confirmed by official city council minutes and three independent news outlets.",
    reasoning: "All factual claims cross-verified with primary source documents.",
    falseDetails: [],
    uncertainDetails: ["Final budget figure pending"],
    tags: ["local", "transit"],
    upvotes: 87,
    downvotes: 1,
    disputes: 0,
    claims: [],
  },
  {
    id: "a5",
    title: "New cryptocurrency promises 1000% returns in 30 days",
    source: "cryptohype.io",
    inputType: "url",
    inputPreview: "https://cryptohype.io/moonshot-2025",
    submittedBy: "warning_bot",
    submittedAt: "6h ago",
    verdict: "mostly-false",
    overallCredibility: 14,
    overallConfidence: 87,
    summary: "Bears all hallmarks of a pump-and-dump scheme. No legitimate returns guarantees exist.",
    reasoning: "Domain registered 11 days ago. Anonymous founders. Liquidity pool concentrated in 3 wallets.",
    falseDetails: ["Guaranteed returns claim", "'Audited by KPMG' — KPMG has no record"],
    uncertainDetails: ["Actual on-chain transaction volume"],
    tags: ["crypto", "scam", "finance"],
    upvotes: 412,
    downvotes: 28,
    disputes: 7,
    claims: [],
  },
];

export const recentActivity = [
  { id: "r1", type: "analysis", title: "Coffee reverses aging study", verdict: "false" as Verdict, time: "2h" },
  { id: "r2", type: "analysis", title: "EU AI Act passed", verdict: "mostly-true" as Verdict, time: "5h" },
  { id: "r3", type: "dispute", title: "Climate report figures", verdict: "mixed" as Verdict, time: "8h" },
  { id: "r4", type: "analysis", title: "Mars flag photo", verdict: "false" as Verdict, time: "1d" },
  { id: "r5", type: "analysis", title: "Transit pilot vote", verdict: "true" as Verdict, time: "3d" },
  { id: "r6", type: "dispute", title: "Vaccine efficacy data", verdict: "mostly-true" as Verdict, time: "4d" },
];
