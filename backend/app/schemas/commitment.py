from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class CommitmentEventSchema(BaseModel):
    id: int
    event_type: str
    event_data: Optional[Any] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class CommitmentListItem(BaseModel):
    id: int
    owner: str
    action: str
    due_date: Optional[datetime] = None
    status: str
    confidence_score: Optional[float] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class CommitmentDetailResponse(BaseModel):
    id: int
    owner: str
    action: str
    due_date: Optional[datetime] = None
    status: str
    confidence_score: Optional[float] = None
    source_transcript_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    events: list[CommitmentEventSchema] = []
    model_config = {"from_attributes": True}


class CommitmentStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None


class DashboardResponse(BaseModel):
    active: int
    fulfilled: int
    missed: int
    detected: int
    due_soon: int
    total: int