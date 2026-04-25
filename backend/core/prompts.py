ESSENCE_PROMPT = """
Read this article and extract its core narrative.

Article:
{article_text}
"""

CLAIM_SPLIT_PROMPT = """
Article essence (preserve this meaning — do NOT lose it in splitting):
{essence}

Split the article below into atomic, independently verifiable claims.

Rules:
- Keep emotionally loaded words (e.g. "secretly", "only the poor", "massive")
- Split on factual assertions, not conjunctions or filler
- Label each claim as "fact" (checkable external event) or "framing" (opinion/spin)
- Identify loaded language inside each claim
- Explain how each claim connects to the overall narrative (essence_relation)
- Maximum 10 claims

Article:
{article_text}
"""

QUERY_BUILDER_PROMPT = """
Generate two search queries for fact-checking this claim.

Claim: {claim}
Article context (essence): {essence}

Rules:
- Confirming query: finds articles, reports, or statements that support the claim
- Contradicting query: finds corrections, rebuttals, fact-checks, or opposing evidence
  Use words like: debunked, false, misleading, correction, "fact check", OR rephrase to find the opposing view
- Queries must be meaningfully different — different vocabulary, different angle
"""

ALIGNMENT_PROMPT = """
You are checking whether search results are actually relevant to a specific claim.

Claim: {claim}

Evidence:
{evidence}

For each piece of evidence, assess its relevance, stance, and source type.
"""

JUDGE_PROMPT = """
You are a rigorous fact-checker. You ONLY use the evidence provided — never your own training knowledge.

Claim: {claim}
Article context: {essence}

Supporting evidence found:
{supporting_evidence}

Contradicting evidence found:
{contradicting_evidence}

Source diversity note: {diversity_note}
Contradiction search note: {contradiction_note}

Verdict rules:
- "supported": multiple independent sources directly confirm the claim
- "contradicted": evidence directly refutes a specific detail in the claim
- "uncertain": evidence exists on both sides, or is too thin to commit
- "unverifiable": no evidence directly addresses this claim

IMPORTANT: A claim can be mostly true with ONE false detail. Identify the specific false detail, not just the whole claim.
"""

AGGREGATOR_PROMPT = """
You are writing a plain-English summary of a fact-check result for an article.

Article essence: {essence}
Article framing tone: {framing_tone}

Per-claim results:
{claim_summaries}

Overall credibility score (0–1): {ai_score}

Write a 3–4 sentence summary that:
- States what the article got right and wrong
- Calls out any framing manipulation separately from factual errors
- Is honest about what could not be verified
"""