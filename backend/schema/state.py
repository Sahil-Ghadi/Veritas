from typing import TypedDict, Annotated, Optional, Literal, List, Any
import operator
from pydantic import BaseModel, Field

# --- Structured Output Models ---

class EssenceOutput(BaseModel):
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
    raw_input: str
    input_type: str

    # ── Cache ──────────────────────────────────────────────
    cached: bool
    cached_result: Optional[dict]
    content_hash: str
    content_hash_written: bool

    # ── Parsed ─────────────────────────────────────────────
    parsed_text: str

    # ── Essence ────────────────────────────────────────────
    essence: str
    framing_tone: str
    primary_actor: str
    implied_consequence: str
    drift_score: float

    # ── Claims ─────────────────────────────────────────────
    claims: List[dict]
    # Parallel branches can emit these in the same step; allow safe merge.
    current_claim: Annotated[Optional[dict], take_latest]
    current_search_results: Annotated[List[dict], take_latest]
    # Fan-in accumulator — operator.add appends each branch's [ClaimResult]
    claim_results: Annotated[List[dict], operator.add]

    # ── Output ─────────────────────────────────────────────
    ai_score: float
    score_breakdown: dict
    article_level_explanation: str
