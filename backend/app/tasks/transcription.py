"""
Celery task: Audio transcription using faster-whisper.
After transcription → automatically triggers commitment extraction.
"""
import os
import traceback

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.upload import Upload


def _get_db() -> Session:
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def transcribe_audio(self, recording_id: int):
    """
    Transcribe audio using Whisper.
    After saving transcript → trigger commitment extraction automatically.
    """
    db = _get_db()
    try:
        # --- 1. Fetch recording ---
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            raise ValueError(f"Recording {recording_id} not found.")

        upload = db.query(Upload).filter(Upload.id == recording.upload_id).first()
        if not upload:
            raise ValueError(f"Upload not found for recording {recording_id}.")

        # --- 2. Mark as processing ---
        upload.processing_status = "processing"
        db.commit()

        audio_path = recording.audio_path
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        # --- 3. Transcribe with Whisper ---
        from faster_whisper import WhisperModel
        print(f"[Whisper] Loading model for recording {recording_id}...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")

        print(f"[Whisper] Transcribing {audio_path}...")
        segments, info = model.transcribe(audio_path)
        transcript_text = " ".join([seg.text for seg in segments]).strip()

        if not transcript_text:
            raise ValueError("Whisper returned empty transcript.")

        # --- 4. Save transcript ---
        transcript = Transcript(
            upload_id=upload.id,
            content=transcript_text,
        )
        db.add(transcript)

        # --- 5. Update duration ---
        recording.duration = info.duration if hasattr(info, 'duration') else None

        # --- 6. Mark upload as completed ---
        upload.processing_status = "completed"
        db.commit()
        db.refresh(transcript)

        print(f"[Whisper] Done. Transcript {transcript.id} saved for recording {recording_id}.")
        print(f"[Whisper] Transcript preview: {transcript_text[:100]}...")

        # --- 7. Trigger commitment extraction automatically ---
        from app.tasks.extraction import extract_commitments
        extract_commitments.delay(transcript.id)
        print(f"[Whisper] Extraction task queued for transcript {transcript.id}")

        return {
            "status": "completed",
            "transcript_id": transcript.id,
            "transcript_length": len(transcript_text),
        }

    except Exception as exc:
        db.rollback()

        # Mark upload as failed
        try:
            rec = db.query(Recording).filter(Recording.id == recording_id).first()
            if rec:
                up = db.query(Upload).filter(Upload.id == rec.upload_id).first()
                if up:
                    up.processing_status = "failed"
                    db.commit()
        except Exception:
            pass

        print(f"[Whisper] Error for recording {recording_id}: {exc}")
        traceback.print_exc()
        raise self.retry(exc=exc)

    finally:
        db.close()