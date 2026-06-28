"""
Celery periodic task: Check for missed commitments.
Runs every hour.

Only marks MISSED if:
- Status is ACTIVE (not DETECTED — wait for activation first)
- Due date has passed
- No fulfillment evidence found
"""
import traceback
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.core.state_machine import transition_commitment, mark_missed_if_overdue
from app.db.database import SessionLocal
from app.models.commitment import Commitment
from app.models.enums import CommitmentStatus


@celery_app.task
def check_missed_commitments():
    """
    Scan ACTIVE commitments.
    If due_date passed → mark MISSED.
    DETECTED commitments are NOT marked missed (they haven't been activated yet).
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Only check ACTIVE commitments — not DETECTED
        overdue = (
            db.query(Commitment)
            .filter(
                Commitment.status == CommitmentStatus.ACTIVE,
                Commitment.due_date.isnot(None),
                Commitment.due_date < now,
            )
            .all()
        )

        count = 0
        for commitment in overdue:
            success = transition_commitment(
                db,
                commitment,
                CommitmentStatus.MISSED,
                event_data={
                    "reason": "due_date_passed",
                    "due_date": str(commitment.due_date)[:10],
                    "checked_at": now.isoformat(),
                },
            )
            if success:
                count += 1
                print(
                    f"[MissedChecker] Commitment {commitment.id} → MISSED "
                    f"(Owner: {commitment.owner}, Due: {commitment.due_date})"
                )

        if count > 0:
            db.commit()

        print(f"[MissedChecker] Done. {count} commitments marked MISSED.")
        return {"missed_count": count}

    except Exception as exc:
        db.rollback()
        print(f"[MissedChecker] Error: {exc}")
        traceback.print_exc()
        raise

    finally:
        db.close()