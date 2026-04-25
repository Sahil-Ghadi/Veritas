from typing import TypedDict, Annotated, Optional, Literal, List, Any
import operator
from pydantic import BaseModel, Field

# --- Structured Output Models ---

class EssenceOutput(BaseModel):
    is_verifiable: bool = Field(..., description="False if this is a personal, anonymous, or non-news statement (e.g. 'I am sick'). True if it makes a checkable public claim.")
    essence: str = Field(..., description="One sentence capturing what the article is alleging")
    framing_tone: Literal["alarmist", "neutral", "misleading", "satirical", "opinion"]
    primary_actor: str = Field(..., description="Who the article is about")
    implied_consequence: str = Field(..., description="What the article wants the reader to fear or believe")

class Claim(BaseModel):
    text: str = Field(..., description="The atomic claim")
    type: Literal["fact", "framing", "attributed"]
    loaded_language: List[str] = Field(default_factory=list)
    essence_relation: str = Field(..., description="How this connects to the overall narrative")

class ClaimSplitOutput(BaseModel):
    claims: List[Claim]

class QueryBuilderOutput(BaseModel):
    confirming_query: str
    contradicting_query: str

class EvidenceAlignment(BaseModel):
    url: str
    relevance: Literal["direct", "partial", "irrelevant"]
    stance: Literal["supports", "contradicts", "neutral"]
    source_type: Literal["primary", "secondary", "aggregator"]

class AlignmentOutput(BaseModel):
    evidence_alignment: List[EvidenceAlignment]
    has_direct_evidence: bool

class JudgeOutput(BaseModel):
    verdict: Literal["supported", "contradicted", "uncertain", "unverifiable"]
    confidence: float
    false_detail: Optional[str] = None
    reasoning: str
    uncertainty_reason: Optional[str] = None

# Combined output — replaces separate AlignmentOutput + JudgeOutput
# Lets the LLM classify evidence AND deliver a verdict in one round-trip.
class EvidenceJudgeOutput(BaseModel):
    evidence_alignment: List[EvidenceAlignment]
    has_direct_evidence: bool
    verdict: Literal["supported", "contradicted", "uncertain", "unverifiable"]
    confidence: float
    false_detail: Optional[str] = None
    reasoning: str
    uncertainty_reason: Optional[str] = None

class ExplanationOutput(BaseModel):
    explanation: str

# --- Graph State ---

class ClaimResult(BaseModel):
    claim: str
    claim_type: Literal["fact", "framing", "attributed"] = "fact"
    verdict: Literal["supported", "contradicted", "uncertain", "unverifiable"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    supporting_sources: List[str] = Field(default_factory=list)
    contradicting_sources: List[str] = Field(default_factory=list)
    false_detail: Optional[str] = None
    uncertainty_reason: Optional[str] = None
    echo_chamber_detected: bool = False


def take_latest(left: Any, right: Any) -> Any:
    """Resolve concurrent branch-local writes by keeping latest value."""
    return right if right is not None else left



class GraphState(TypedDict, total=False):
    # total=False makes all fields Optional at the TypedDict level,
    # avoiding KeyError on partial state (cache-hit path, subgraph entry, etc.)
    # Fields that MUST be present at pipeline start are validated in _run_pipeline.

    # ── Input ──────────────────────────────────────────────
    raw_input: Annotated[str, take_latest]
    input_type: Annotated[str, take_latest]

    # ── Cache ──────────────────────────────────────────────
    cached: Annotated[bool, take_latest]
    cached_result: Annotated[Optional[dict], take_latest]
    content_hash: Annotated[str, take_latest]
    content_hash_written: Annotated[bool, take_latest]

    # ── Parsed ─────────────────────────────────────────────
    parsed_text: Annotated[str, take_latest]

    # ── Essence ────────────────────────────────────────────
    is_verifiable: Annotated[bool, take_latest]
    essence: Annotated[str, take_latest]
    framing_tone: Annotated[str, take_latest]
    primary_actor: Annotated[str, take_latest]
    implied_consequence: Annotated[str, take_latest]
    drift_score: Annotated[float, take_latest]

    # ── Claims ─────────────────────────────────────────────
    claims: Annotated[List[dict], take_latest]
    # Parallel branches can emit these in the same step; allow safe merge.
    current_claim: Annotated[Optional[dict], take_latest]
    current_search_results: Annotated[List[dict], take_latest]
    # Fan-in accumulator — appends each branch's [ClaimResult]
    claim_results: Annotated[List[dict], lambda x, y: (x or []) + (y or [])]

    # ── Output ─────────────────────────────────────────────
    ai_score: Annotated[float, take_latest]
    score_breakdown: Annotated[dict, take_latest]
    article_level_explanation: Annotated[str, take_latest]
