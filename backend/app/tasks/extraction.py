"""
Celery task: Extract commitments from transcript using AI.
Includes: extraction, fulfillment detection, modification detection.
"""
import traceback
from datetime import datetime
from difflib import SequenceMatcher

from app.celery_app import celery_app
from app.core.ai_extractor import (
    extract_commitments_from_text,
    validate_commitment,
    check_fulfillment_with_ai,
    check_modifications_with_ai,
)
from app.core.state_machine import transition_commitment
from app.db.database import SessionLocal
from app.models.commitment import Commitment
from app.models.commitment_event import CommitmentEvent
from app.models.enums import CommitmentStatus
from app.models.transcript import Transcript
from app.models.upload import Upload

SIMILARITY_THRESHOLD = 0.45


def _get_db():
    return SessionLocal()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _get_open_commitments_for_user(db, transcript_id: int) -> list[dict]:
    open_statuses = [
        CommitmentStatus.DETECTED,
        CommitmentStatus.CONFIRMED,
        CommitmentStatus.ACTIVE,
        CommitmentStatus.MODIFIED,
        CommitmentStatus.BLOCKED,
    ]

    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        return []

    upload = db.query(Upload).filter(Upload.id == transcript.upload_id).first()
    if not upload:
        return []

    commitments = (
        db.query(Commitment)
        .join(Transcript, Commitment.source_transcript_id == Transcript.id)
        .join(Upload, Transcript.upload_id == Upload.id)
        .filter(
            Upload.user_id == upload.user_id,
            Commitment.status.in_(open_statuses),
            Commitment.source_transcript_id != transcript_id,
        )
        .all()
    )

    return [
        {
            "id": c.id,
            "owner": c.owner,
            "action": c.action,
            "due_date": str(c.due_date)[:10] if c.due_date else None,
        }
        for c in commitments
    ]


@celery_app.task(bind=True, max_retries=3, default_retry_delay=15)
def extract_commitments(self, transcript_id: int):
    db = _get_db()
    try:
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found.")

        print(f"[Extraction] Processing transcript {transcript_id}...")

        open_commitments = _get_open_commitments_for_user(db, transcript_id)
        print(f"[Extraction] Found {len(open_commitments)} open commitments to check.")

        fulfilled_ids = []
        modified_ids = []

        if open_commitments:

            # -------------------------
            # Step 1: Modification First
            # -------------------------
            modifications = check_modifications_with_ai(
                transcript.content,
                open_commitments
            )

            modified_ids_temp = {
                m["id"]
                for m in modifications
                if m.get("id")
            }

            # -------------------------
            # Step 2: Fulfillment
            # Skip already modified
            # -------------------------
            remaining = [
                c
                for c in open_commitments
                if c["id"] not in modified_ids_temp
            ]

            fulfilled_ids = check_fulfillment_with_ai(
                transcript.content,
                remaining
            )

        else:
            fulfilled_ids = []
            modifications = []
            
            print(f"[Extraction] Modifications found: {modifications}")

        fulfilled_count = 0
        modified_count = 0
        new_count = 0

        # --- Process fulfillments ---
        for fid in fulfilled_ids:
            commitment = db.query(Commitment).filter(Commitment.id == fid).first()
            if commitment:
                success = transition_commitment(
                    db,
                    commitment,
                    CommitmentStatus.FULFILLED,
                    event_data={
                        "evidence_transcript_id": transcript_id,
                        "auto_detected": True,
                        "method": "ai_fulfillment_check",
                    },
                )
                if success:
                    fulfilled_count += 1
                    modified_ids.append(fid)
                    print(f"[Extraction] ✅ Commitment {fid} → FULFILLED")

        # --- Process modifications ---
        for mod in modifications:
            mod_id = mod.get("id")
            if not mod_id or mod_id in fulfilled_ids:
                continue

            commitment = db.query(Commitment).filter(Commitment.id == mod_id).first()
            if not commitment:
                continue

            new_due_date = None
            if mod.get("new_due_date"):
                try:
                    new_due_date = datetime.strptime(mod["new_due_date"], "%Y-%m-%d")
                except ValueError:
                    new_due_date = None

            success = transition_commitment(
                db,
                commitment,
                CommitmentStatus.MODIFIED,
                due_date=new_due_date,
                event_data={
                    "new_action": mod.get("new_action"),
                    "old_due_date": str(commitment.due_date)[:10] if commitment.due_date else None,
                    "new_due_date": mod.get("new_due_date"),
                    "reason": mod.get("reason"),
                    "transcript_id": transcript_id,
                },
            )
            if success:
                modified_count += 1
                modified_ids.append(mod_id)
                print(
                    f"[Extraction] 🔄 Commitment {mod_id} → MODIFIED "
                    f"(reason: {mod.get('reason')})"
                )

                # Update action text if changed
                if mod.get("new_action") and commitment:
                    commitment.action = mod["new_action"]

        # --- Step 3: Extract new commitments ---
        raw_commitments = extract_commitments_from_text(transcript.content)
        print(f"[Extraction] LLM returned {len(raw_commitments)} raw commitments.")

        for raw in raw_commitments:
            validated = validate_commitment(raw)
            if not validated:
                continue

            due_date = None
            if validated["due_date"]:
                try:
                    due_date = datetime.strptime(validated["due_date"], "%Y-%m-%d")
                except ValueError:
                    due_date = None

            owner = validated["owner"]
            action = validated["action"]

            # Skip if already handled above
            already_handled = any(
                c["owner"].lower() == owner.lower() and
                _similarity(c["action"], action) > 0.6
                for c in open_commitments
                if c["id"] in modified_ids
            )
            if already_handled:
                print(f"[Extraction] Skipping handled: {owner} - {action}")
                continue

            # New commitment
            commitment = Commitment(
                owner=owner,
                action=action,
                due_date=due_date,
                confidence_score=validated["confidence"],
                status=CommitmentStatus.DETECTED,
                source_transcript_id=transcript_id,
            )
            db.add(commitment)
            db.flush()

            event = CommitmentEvent(
                commitment_id=commitment.id,
                event_type="created",
                event_data={
                    "owner": owner,
                    "action": action,
                    "due_date": validated["due_date"],
                    "confidence": validated["confidence"],
                    "source": "ai_extraction",
                },
            )
            db.add(event)
            new_count += 1
            print(f"[Extraction] 🆕 New: {owner} - {action}")

        db.commit()
        print(
            f"[Extraction] Done — "
            f"New: {new_count}, "
            f"Fulfilled: {fulfilled_count}, "
            f"Modified: {modified_count}"
        )
        return {
            "status": "completed",
            "new": new_count,
            "fulfilled": fulfilled_count,
            "modified": modified_count,
        }

    except Exception as exc:
        db.rollback()
        print(f"[Extraction] Error: {exc}")
        traceback.print_exc()
        raise self.retry(exc=exc)

    finally:
        db.close()