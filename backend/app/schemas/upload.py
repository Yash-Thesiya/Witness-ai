from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AudioUploadResponse(BaseModel):
    upload_id: int
    recording_id: int
    file_name: str
    processing_status: str
    message: str
    model_config = {"from_attributes": True}


class TranscriptUploadResponse(BaseModel):
    upload_id: int
    transcript_id: int
    file_name: str
    characters_extracted: int
    message: str
    model_config = {"from_attributes": True}


class UploadListItem(BaseModel):
    id: int
    file_name: str
    file_type: str
    processing_status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class UploadDetailResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    processing_status: str
    created_at: datetime
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    transcript_id: Optional[int] = None
    transcript_preview: Optional[str] = None
    model_config = {"from_attributes": True}
