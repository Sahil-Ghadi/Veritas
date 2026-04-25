import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DisputeType(str, Enum):
    VERDICT = "VERDICT"
    SOURCE_QUALITY = "SOURCE_QUALITY"
    UNCERTAINTY = "UNCERTAINTY"


class DisputeStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class DisputeErrorCode(str, Enum):
    SELF_DISPUTE = "SELF_DISPUTE"
    ALREADY_DISPUTED = "ALREADY_DISPUTED"
    RATE_LIMIT_REACHED = "RATE_LIMIT_REACHED"
    ACCOUNT_TOO_NEW = "ACCOUNT_TOO_NEW"
    POST_UNDER_REVIEW = "POST_UNDER_REVIEW"
    POST_NOT_FOUND = "POST_NOT_FOUND"


@dataclass
class Dispute:
    post_id: str
    disputer_id: str
    claim_index: int
    dispute_type: DisputeType
    counter_argument: str
    status: DisputeStatus
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    counter_source_url: Optional[str] = None
    validation_result: Optional[dict] = None
    score_impact: Optional[float] = None
    created_at: Optional[datetime] = None
