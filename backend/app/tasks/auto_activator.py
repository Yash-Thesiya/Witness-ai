"""
Celery periodic task: Auto-activate DETECTED commitments after 2 hours.

Flow:
DETECTED (extracted by AI)
    ↓ 2 hours baad automatically
ACTIVE (tracking shuru)
"""
import traceback
from datetime import datetime, timezone, timedelta

from app.celery_app import celery_app
from app.core.state_machine import transition_commitment
from app.db.database import SessionLocal
from app.models.commitment import Commitment
from app.models.enums import CommitmentStatus


@celery_app.task
def auto_activate_commitments():
    """
    Find all DETECTED commitments older than 2 hours.
    Transition them to ACTIVE automatically.
    """
    db = SessionLocal()
    try:
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)

        detected_commitments = (
            db.query(Commitment)
            .filter(
                Commitment.status == CommitmentStatus.DETECTED,
                Commitment.created_at <= two_hours_ago,
            )
            .all()
        )

        count = 0
        for commitment in detected_commitments:
            success = transition_commitment(
                db,
                commitment,
                CommitmentStatus.ACTIVE,
                event_data={
                    "reason": "auto_activated_after_2hrs",
                    "activated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            if success:
                count += 1
                print(
                    f"[AutoActivator] Commitment {commitment.id} → ACTIVE "
                    f"(Owner: {commitment.owner}, Action: {commitment.action})"
                )

        if count > 0:
            db.commit()

        print(f"[AutoActivator] Done. {count} commitments activated.")
        return {"activated": count}

    except Exception as exc:
        db.rollback()
        print(f"[AutoActivator] Error: {exc}")
        traceback.print_exc()
        raise

    finally:
        db.close()