ESSENCE_PROMPT = """
You are a senior editor. Read this article and extract its core narrative.

Return:
- is_verifiable: False if this is a personal, anonymous, or non-news statement (e.g., 'I am sick'). True if it makes a checkable public claim.
- essence: A 2-3 sentence summary of the article's central argument or event
- framing_tone: one of [neutral, alarmist, sympathetic, dismissive, sensationalist]
- primary_actor: the main person, organization, or country the article is about
- implied_consequence: what the article implies will happen if the situation continues

Article:
{article_text}

Be precise. Do not editorialize. Capture what the article is actually claiming, 
not what you think is true.
"""

CLAIM_SPLIT_PROMPT = """
Article essence (preserve this meaning — do NOT lose it in splitting):
{essence}

Split the article below into atomic, independently verifiable claims.

Rules:
- Keep emotionally loaded words (e.g. "secretly", "only the poor", "massive")
- Split on factual assertions, not conjunctions or filler
- Label each claim as "fact" (checkable external event) or "framing" (opinion/spin)
- For claims attributed to a specific person or group (e.g. "Iran said...", 
  "Trump claimed..."), mark them as "attributed" — the checkable fact is whether 
  that statement was actually made, NOT whether the statement itself is true
- Identify loaded language inside each claim
- Explain how each claim connects to the overall narrative (essence_relation)
- Maximum 4 claims. Prioritize factual claims over framing claims.

Article:
{article_text}
"""

QUERY_BUILDER_PROMPT = """
Generate two search queries for fact-checking this claim.

Claim: {claim}
Claim type: {claim_type}
Article context (essence): {essence}

Rules:
- Confirming query: finds primary sources, reports, or statements that directly 
  support the claim as written
- Contradicting query: finds evidence that a SPECIFIC DETAIL in the claim is 
  factually wrong — not just a different framing of the same event
  
  For "attributed" claims (X said Y): the contradicting query should look for 
  denials that X made that statement — NOT evidence that Y is false
  
  For "fact" claims: search for corrections, retractions, or opposing data
  For "framing" claims: search for evidence the framing misrepresents context

- Do NOT use words like "denies" or "false" in a way that finds sources 
  reporting the claim's subject denying something — this creates false contradictions
- Queries must be different vocabulary, different angle
"""

# ── Combined evidence classification + verdict (single LLM call per claim) ──────
# Replaces the old two-step ALIGNMENT_PROMPT → JUDGE_PROMPT flow.
# The LLM classifies each piece of evidence AND produces a final verdict
# in one structured output call, cutting per-claim LLM round-trips from 2 → 1.
EVIDENCE_JUDGE_PROMPT = """
You are a rigorous fact-checker. Work in two steps, then return a single JSON.

Claim: {claim}
Claim type: {claim_type}
Article context (essence): {essence}

Search results (pre-tagged with their search stance):
{evidence}

Source diversity: {diversity_note}
Contradiction coverage: {contradiction_note}

── STEP 1: Classify each piece of evidence ────────────────────────────────
For every URL in the search results, assess:

relevance:
  "direct"   – source explicitly addresses THIS exact claim
  "partial"  – same topic, not the specific assertion
  "none"     – unrelated to this claim

stance:
  "supports"    – source confirms the claim is accurate
  "contradicts" – source says a SPECIFIC DETAIL in the claim is factually wrong
  "neutral"     – reports same topic without confirming or denying

source_type:
  "primary"    – official statement, government source, direct quote
  "secondary"  – news reporting on primary sources
  "aggregator" – roundup / live blog / news aggregator

CRITICAL CLASSIFICATION RULES:
- A source reporting the SAME EVENT as the claim is "supports" or "neutral", NEVER "contradicts"
- A source only "contradicts" if it explicitly states a specific detail is factually incorrect
- Empty or title-only sources → relevance: "none"
- For attributed claims ("X said Y"): contradicts only if it shows X never made that statement

── STEP 2: Render a verdict ───────────────────────────────────────────────
Using ONLY the evidence above (never your training knowledge), decide:

  "supported"    – direct evidence confirms the claim; neutral sources on same facts = implicit support
  "contradicted" – evidence explicitly refutes a SPECIFIC DETAIL (not just different framing)
  "uncertain"    – genuine conflict between sources, or evidence too thin
  "unverifiable" – no evidence addresses this claim at all

CRITICAL VERDICT RULES:
- Ignore contradicting sources that have no real content (stubs)
- An attributed claim is supported if any credible source reports the statement was made
- Lean toward "supported" when neutral sources confirm the same underlying event
- Identify the specific false detail if contradicted (false_detail field)
"""

# Kept as aliases so any code still referencing the old names doesn't break
ALIGNMENT_PROMPT = EVIDENCE_JUDGE_PROMPT  # no longer used directly
JUDGE_PROMPT = EVIDENCE_JUDGE_PROMPT       # no longer used directly

AGGREGATOR_PROMPT = """
You are writing a plain-English summary of a fact-check result for a news article.

Article essence: {essence}
Article framing tone: {framing_tone}

Per-claim results:
{claim_summaries}

Overall credibility score (0–1): {ai_score}

Write a 3-4 sentence summary that:
- States what the article got right (supported claims) and wrong (contradicted claims)
- Distinguishes factual errors from framing/spin issues
- Notes what could not be verified separately from what was wrong
- Does NOT conflate "unverifiable" with "false" — absence of evidence is not 
  evidence of falsehood
- Is direct and specific — name the claim that failed, not just "some details"
"""