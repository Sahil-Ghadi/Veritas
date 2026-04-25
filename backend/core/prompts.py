ESSENCE_PROMPT = """
You are a senior editor. Read this article and extract its core narrative.

Return:
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

ALIGNMENT_PROMPT = """
You are checking whether search results are actually relevant to a specific claim.

Claim: {claim}
Claim type: {claim_type}

Evidence:
{evidence}

For each piece of evidence, assess:

relevance:
- "direct": the source explicitly addresses this exact claim
- "partial": the source addresses the same topic but not the specific assertion
- "none": the source is not about this claim at all

stance:
- "supports": the source confirms the claim is accurate
- "contradicts": the source says a specific detail in the claim is WRONG
- "neutral": the source reports on the same topic without confirming or denying

source_type:
- "primary": official statement, government source, direct quote
- "secondary": news reporting on primary sources  
- "aggregator": roundup, live blog, news aggregator

CRITICAL RULES:
- A source that reports the SAME EVENT as the claim is "supports" or "neutral", 
  never "contradicts" — even if its headline sounds like a denial
- A source only "contradicts" if it explicitly states a specific detail in the 
  claim is factually incorrect
- Empty or stub sources (no article body) must be marked relevance: "none"
- For attributed claims ("X said Y"): a source contradicts only if it shows 
  X never made that statement — not if it shows Y is debatable
"""

JUDGE_PROMPT = """
You are a rigorous fact-checker. You ONLY use the evidence provided — 
never your own training knowledge.

Claim: {claim}
Claim type: {claim_type}
Article context: {essence}

Supporting evidence:
{supporting_evidence}

Neutral/contextual evidence (read carefully — may contain implicit confirmation):
{neutral_context}

Contradicting evidence:
{contradicting_evidence}

Source diversity note: {diversity_note}
Contradiction search note: {contradiction_note}

Verdict rules:
- "supported": direct evidence confirms the claim. Neutral sources reporting 
  the same underlying facts count as implicit support.
- "contradicted": evidence explicitly refutes a SPECIFIC DETAIL. A source 
  reporting the same event with different framing is NOT contradiction.
- "uncertain": genuine conflict between sources, or evidence too thin to decide
- "unverifiable": no evidence addresses this claim at all

CRITICAL: 
- Check if contradicting sources actually have content — empty stubs must be ignored
- A claim attributed to a speaker (e.g. "Iran said...") is supported if any 
  credible source reports that statement was made
- Identify the specific false detail if contradicted, not just the whole claim
- If neutral sources confirm the same underlying event, lean toward "supported" 
  not "uncertain"
"""

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