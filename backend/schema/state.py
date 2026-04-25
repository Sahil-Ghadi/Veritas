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
    type: Literal["fact", "framing"]
    loaded_language: List[str] = Field(default_factory=list)
    essence_relation: str = Field(..., description="How this connects to the overall narrative")

class ClaimSplitOutput(BaseModel):
    claims: List[Claim]

class QueryBuilderOutput(BaseModel):
    confirming_query: str
    contradicting_query: str

class EvidenceAlignment(BaseModel):
    url: str
    relevance: Literal["direct", "partial", "none"]
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
    claim_type: Literal["fact", "framing"] = "fact"
    verdict: Literal["supported", "contradicted", "uncertain", "unverifiable"]
    confidence: float
    reasoning: str
    supporting_sources: List[str] = Field(default_factory=list)
    contradicting_sources: List[str] = Field(default_factory=list)
    false_detail: Optional[str] = None
    uncertainty_reason: Optional[str] = None
    diversity_score: float = 1.0
    echo_chamber_detected: bool = False


def take_latest(left: Any, right: Any) -> Any:
    """Reducer for branch-local keys written concurrently."""
    return right if right is not None else left

class GraphState(TypedDict):
    raw_input: str
    input_type: str
    parsed_text: str
    content_hash: str
    essence: str
    framing_tone: str
    primary_actor: str
    implied_consequence: str
    claims: List[dict]
    current_claim: Annotated[Optional[dict], take_latest]
    current_search_results: Annotated[List[dict], take_latest]
    claim_results: Annotated[List[dict], operator.add]
    ai_score: float
    score_breakdown: dict
    article_level_explanation: str
    cached: bool
    cached_result: Optional[dict]
    drift_score: float
    content_hash_written: bool
