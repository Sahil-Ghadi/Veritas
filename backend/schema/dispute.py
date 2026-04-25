from typing import Optional

from models.dispute import DisputeErrorCode, DisputeStatus, DisputeType
from pydantic import BaseModel, HttpUrl, field_validator


class DisputeRequest(BaseModel):
    post_id: str
    claim_index: int
    dispute_type: DisputeType
    counter_argument: str
    counter_source_url: Optional[HttpUrl] = None

    @field_validator("counter_argument")
    @classmethod
    def validate_counter_argument_length(cls, v: str) -> str:
        if len(v.strip()) < 20:
            raise ValueError("counter_argument must be at least 20 characters long")
        return v


class DisputeRejectedResponse(BaseModel):
    status: str = "REJECTED"
    reason: str


class DisputeValidatedResponse(BaseModel):
    status: str = "VALIDATED"
    score_impact: float
    new_score: float


class DisputeErrorResponse(BaseModel):
    error: str
    code: DisputeErrorCode
