from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.file_handler import (
    AUDIO_DIR, TRANSCRIPT_DIR,
    extract_text_from_file, save_file,
    validate_audio_file, validate_transcript_file,
)
from app.db.database import get_db
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.upload import Upload
from app.models.user import User
from app.schemas.upload import (
    AudioUploadResponse, TranscriptUploadResponse,
    UploadDetailResponse, UploadListItem,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/audio", response_model=AudioUploadResponse, status_code=201)
def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_audio_file(file)
    saved_path, original_name = save_file(file, AUDIO_DIR)
    try:
        upload = Upload(
            user_id=current_user.id,
            file_name=original_name,
            file_type="audio",
            processing_status="pending",
        )
        db.add(upload)
        db.flush()
        recording = Recording(upload_id=upload.id, audio_path=saved_path)
        db.add(recording)
        db.commit()
        db.refresh(upload)
        db.refresh(recording)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    try:
        from app.tasks.transcription import transcribe_audio
        transcribe_audio.delay(recording.id)
    except Exception as exc:
        print(f"[Warning] Could not queue transcription task: {exc}")

    return AudioUploadResponse(
        upload_id=upload.id,
        recording_id=recording.id,
        file_name=original_name,
        processing_status="pending",
        message="Audio uploaded. Transcription queued in background.",
    )


@router.post("/transcript", response_model=TranscriptUploadResponse, status_code=201)
def upload_transcript(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_transcript_file(file)
    extracted_text = extract_text_from_file(file)
    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from file.")
    saved_path, original_name = save_file(file, TRANSCRIPT_DIR)
    try:
        upload = Upload(
            user_id=current_user.id,
            file_name=original_name,
            file_type="transcript",
            processing_status="completed",
        )
        db.add(upload)
        db.flush()
        transcript = Transcript(upload_id=upload.id, content=extracted_text)
        db.add(transcript)
        db.commit()
        db.refresh(upload)
        db.refresh(transcript)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    # Trigger AI commitment extraction
    try:
        from app.tasks.extraction import extract_commitments
        extract_commitments.delay(transcript.id)
        print(f"[Upload] Extraction task queued for transcript {transcript.id}")
    except Exception as exc:
        print(f"[Warning] Could not queue extraction task: {exc}")

    return TranscriptUploadResponse(
        upload_id=upload.id,
        transcript_id=transcript.id,
        file_name=original_name,
        characters_extracted=len(extracted_text),
        message="Transcript uploaded. AI commitment extraction queued.",
    )


@router.get("/", response_model=list[UploadListItem])
def list_uploads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Upload)
        .filter(Upload.user_id == current_user.id)
        .order_by(Upload.created_at.desc())
        .all()
    )


@router.get("/{upload_id}", response_model=UploadDetailResponse)
def get_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found.")
    if upload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    response = UploadDetailResponse(
        id=upload.id,
        file_name=upload.file_name,
        file_type=upload.file_type,
        processing_status=upload.processing_status,
        created_at=upload.created_at,
    )
    if upload.recording:
        response.audio_path = upload.recording.audio_path
        response.duration = upload.recording.duration
    if upload.transcript:
        response.transcript_id = upload.transcript.id
        response.transcript_preview = upload.transcript.content[:200]
    return response