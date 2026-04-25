import { auth } from "@/lib/firebase";
import { Analysis, ActivityItem, Claim, Evidence, Verdict } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type AnalyzeRequest = {
  input_type: "url" | "text" | "image";
  raw_input: string;
};

type AnalyzeResponse = {
  job_id: string;
  status: string;
};

type AnalyzeResultResponse = {
  job_id: string;
  status: string;
  step?: string;
  post_id?: string;
  cached?: boolean;
  content_hash?: string;
  submitted_by?: string;
  my_vote?: "up" | "down" | "none";
  result?: {
    ai_score?: number;
    essence?: string;
    explanation?: string;
    claims?: Array<{
      claim?: string;
      verdict?: "supported" | "contradicted" | "uncertain" | "unverifiable";
      confidence?: number;
      reasoning?: string;
      supporting_sources?: string[];
      contradicting_sources?: string[];
      false_detail?: string | null;
      uncertainty_reason?: string | null;
    }>;
  };
  error?: string;
};

type AnalysisListItem = {
  job_id: string;
  status: string;
  step?: string;
  input_type?: "url" | "text" | "image";
  raw_input?: string;
  created_at?: string;
  result?: AnalyzeResultResponse["result"];
  content_hash?: string;
  cached?: boolean;
  post_id?: string;
  submitted_by?: string;
  my_vote?: "up" | "down" | "none";
  upvotes?: number;
  downvotes?: number;
  disputes?: number;
};

const mapVerdict = (value?: "supported" | "contradicted" | "uncertain" | "unverifiable"): Verdict => {
  if (value === "supported") return "mostly-true";
  if (value === "contradicted") return "false";
  if (value === "uncertain") return "mixed";
  return "unverified";
};

const extractSourceFromInput = (inputType: Analysis["inputType"], rawInput: string): string => {
  if (inputType !== "url") return inputType;
  try {
    return new URL(rawInput).hostname;
  } catch {
    return "unknown";
  }
};

const toEvidence = (url: string, index: number, stance: "supports" | "contradicts"): Evidence => ({
  id: `${stance}-${index}`,
  source: (() => {
    try {
      return new URL(url).hostname;
    } catch {
      return "source";
    }
  })(),
  url,
  title: url,
  stance,
  excerpt: "Source found during verification search.",
  credibility: stance === "supports" ? 75 : 70,
});

const toClaim = (
  claim: NonNullable<AnalyzeResultResponse["result"]>["claims"][number],
  index: number
): Claim => ({
  id: `c-${index + 1}`,
  text: claim.claim || `Claim ${index + 1}`,
  verdict: mapVerdict(claim.verdict),
  confidence: Math.round((claim.confidence ?? 0.5) > 1 ? (claim.confidence ?? 0.5) : (claim.confidence ?? 0.5) * 100),
  credibilityScore: claim.verdict === "supported" ? 80 : claim.verdict === "contradicted" ? 20 : 50,
  reasoning: claim.reasoning || "No reasoning provided by the backend.",
  supporting: (claim.supporting_sources || []).map((url, i) => toEvidence(url, i, "supports")),
  contradicting: (claim.contradicting_sources || []).map((url, i) => toEvidence(url, i, "contradicts")),
  uncertainDetails: claim.uncertainty_reason ? [claim.uncertainty_reason] : [],
});

const toAnalysis = (item: AnalysisListItem): Analysis => {
  const inputType: Analysis["inputType"] = item.input_type || "text";
  const rawInput = item.raw_input || "";
  const claims = (item.result?.claims || []).map(toClaim);
  const claimVerdicts = claims.map((c) => c.verdict);
  const hasFalse = claimVerdicts.includes("false") || claimVerdicts.includes("mostly-false");
  const hasTrue = claimVerdicts.includes("true") || claimVerdicts.includes("mostly-true");
  const overallVerdict: Verdict = hasFalse && hasTrue ? "mixed" : hasFalse ? "false" : hasTrue ? "mostly-true" : "unverified";
  const aiScore = item.result?.ai_score ?? 0.5;
  const credibility = Math.round(aiScore > 1 ? aiScore : aiScore * 100);

  return {
    id: item.job_id,
    postId: item.post_id || item.job_id,
    title: item.result?.essence || "Analysis result",
    source: extractSourceFromInput(inputType, rawInput),
    inputType,
    inputPreview: rawInput,
    submittedBy: item.submitted_by || "community",
    submittedAt: item.created_at ? new Date(item.created_at).toLocaleString() : "just now",
    verdict: overallVerdict,
    overallCredibility: credibility,
    overallConfidence: claims.length > 0 ? Math.round(claims.reduce((sum, c) => sum + c.confidence, 0) / claims.length) : 50,
    summary: item.result?.explanation || "Analysis completed.",
    reasoning: item.result?.explanation || "No detailed explanation provided.",
    falseDetails: (item.result?.claims || []).map((c) => c.false_detail).filter((v): v is string => Boolean(v)),
    uncertainDetails: (item.result?.claims || []).map((c) => c.uncertainty_reason).filter((v): v is string => Boolean(v)),
    claims,
    upvotes: Number(item.upvotes || 0),
    downvotes: Number(item.downvotes || 0),
    disputes: Number(item.disputes || 0),
    tags: ["analysis"],
    myVote: item.my_vote || "none",
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const raw = await response.text();
    let parsed: { detail?: string | { error?: string; code?: string }; error?: string } | null = null;
    try {
      parsed = JSON.parse(raw) as { detail?: string | { error?: string; code?: string }; error?: string };
    } catch {
      parsed = null;
    }
    if (parsed) {
      if (typeof parsed.detail === "string") {
        throw new Error(parsed.detail);
      }
      if (parsed.detail && typeof parsed.detail === "object" && parsed.detail.error) {
        const code = parsed.detail.code ? ` (${parsed.detail.code})` : "";
        throw new Error(`${parsed.detail.error}${code}`);
      }
      if (parsed.error) {
        throw new Error(parsed.error);
      }
    }
    throw new Error(raw || `Request failed with status ${response.status}`);
  }
  return response.json();
}

async function getAuthHeader(): Promise<Record<string, string>> {
  const token = await auth.currentUser?.getIdToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function startAnalysis(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  const authHeader = await getAuthHeader();
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader },
    body: JSON.stringify(payload),
  });
}

export async function getAnalysisResult(jobId: string): Promise<AnalyzeResultResponse> {
  const authHeader = await getAuthHeader();
  return request<AnalyzeResultResponse>(`/api/results/${jobId}`, {
    headers: { ...authHeader },
  });
}

export async function pollAnalysisUntilDone(
  jobId: string,
  maxAttempts = 200,
  onProgress?: (status: AnalyzeResultResponse) => void
): Promise<AnalyzeResultResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const result = await getAnalysisResult(jobId);
    onProgress?.(result);
    if (result.status === "done" || result.status === "error") return result;
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error("Analysis timed out. Please try again.");
}

export async function getAllAnalyses(): Promise<Analysis[]> {
  const authHeader = await getAuthHeader();
  const items = await request<AnalysisListItem[]>("/api/results", {
    headers: { ...authHeader },
  });
  const deduped = new Map<string, AnalysisListItem>();
  for (const item of items) {
    if (item.status !== "done" || !item.result) continue;
    if (item.cached) continue;
    const key = item.content_hash || item.post_id || item.job_id;
    const existing = deduped.get(key);
    if (!existing) {
      deduped.set(key, item);
      continue;
    }
    const existingTs = new Date(existing.created_at || 0).getTime();
    const itemTs = new Date(item.created_at || 0).getTime();
    if (itemTs > existingTs) deduped.set(key, item);
  }
  return Array.from(deduped.values())
    .sort((a, b) => (new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()))
    .map(toAnalysis);
}

export async function getAnalysisById(id: string): Promise<Analysis | null> {
  const result = await getAnalysisResult(id);
  if (result.status !== "done" || !result.result) return null;
  // Also try to pull fresh social counts from the list endpoint for this post
  // so that upvotes/downvotes/disputes reflect live data on the detail page.
  let upvotes = 0, downvotes = 0, disputes = 0;
  try {
    const authHeader = await getAuthHeader();
    const allItems = await request<AnalysisListItem[]>("/api/results", { headers: { ...authHeader } });
    const postId = result.post_id || result.job_id;
    const match = allItems.find((i) => i.post_id === postId || i.job_id === id);
    if (match) {
      upvotes = match.upvotes ?? 0;
      downvotes = match.downvotes ?? 0;
      disputes = match.disputes ?? 0;
    }
  } catch {
    // non-critical — social counts will just show 0
  }
  return toAnalysis({
    job_id: result.job_id,
    status: result.status,
    post_id: result.post_id || result.job_id,
    cached: result.cached || false,
    content_hash: result.content_hash,
    submitted_by: result.submitted_by,
    my_vote: result.my_vote,
    upvotes,
    downvotes,
    disputes,
    result: result.result,
  });
}

export async function submitDispute(payload: {
  post_id: string;
  claim_index: number;
  dispute_type: "VERDICT" | "SOURCE_QUALITY" | "UNCERTAINTY";
  counter_argument: string;
  counter_source_url?: string;
}) {
  const token = await auth.currentUser?.getIdToken();
  return request<{ status: string; reason?: string; score_impact?: number; new_score?: number }>("/api/disputes", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });
}

export async function castVote(postId: string, vote: "up" | "down" | "none") {
  if (!auth.currentUser) {
    throw new Error("Please sign in to vote.");
  }
  const token = await auth.currentUser?.getIdToken();
  return request<{ post_id: string; upvotes: number; downvotes: number; my_vote: "up" | "down" | "none" }>(
    `/api/posts/${postId}/vote`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ vote }),
    }
  );
}

export function buildRecentActivity(analyses: Analysis[]): ActivityItem[] {
  return analyses.slice(0, 6).map((analysis) => ({
    id: analysis.id,
    type: "analysis",
    title: analysis.title,
    verdict: analysis.verdict,
    time: analysis.submittedAt,
  }));
}
