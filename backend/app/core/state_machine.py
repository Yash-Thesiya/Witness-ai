"""
Commitment State Machine.

Manages valid state transitions:

Detected → Confirmed → Active
Active → Modified
Active → Blocked
Active → Fulfilled  (terminal)
Active → Missed     (can recover to Fulfilled)
Active → Cancelled  (terminal)
Modified → Active
Blocked → Active
Missed → Fulfilled  (late completion allowed)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.commitment import Commitment
from app.models.commitment_event import CommitmentEvent
from app.models.enums import CommitmentStatus


# Valid transitions map
VALID_TRANSITIONS = {
    CommitmentStatus.DETECTED: [
        CommitmentStatus.CONFIRMED,
        CommitmentStatus.ACTIVE,
        CommitmentStatus.MODIFIED,      # add kiya
        CommitmentStatus.FULFILLED,
        CommitmentStatus.CANCELLED,
    ],
    CommitmentStatus.CONFIRMED: [
        CommitmentStatus.ACTIVE,
        CommitmentStatus.MODIFIED,      # add kiya
        CommitmentStatus.FULFILLED,
        CommitmentStatus.CANCELLED,
    ],
    CommitmentStatus.ACTIVE: [
        CommitmentStatus.MODIFIED,
        CommitmentStatus.BLOCKED,
        CommitmentStatus.FULFILLED,
        CommitmentStatus.MISSED,
        CommitmentStatus.CANCELLED,
    ],
    CommitmentStatus.MODIFIED: [
        CommitmentStatus.ACTIVE,
        CommitmentStatus.FULFILLED,
        CommitmentStatus.CANCELLED,
    ],
    CommitmentStatus.BLOCKED: [
        CommitmentStatus.ACTIVE,
        CommitmentStatus.FULFILLED,
        CommitmentStatus.CANCELLED,
    ],
    CommitmentStatus.MISSED: [
        CommitmentStatus.FULFILLED,
    ],
    CommitmentStatus.FULFILLED: [],
    CommitmentStatus.CANCELLED: [],
}

TERMINAL_STATES = {CommitmentStatus.FULFILLED, CommitmentStatus.CANCELLED}


def can_transition(current: CommitmentStatus, target: CommitmentStatus) -> bool:
    """Return True if the transition from current to target is valid."""
    return target in VALID_TRANSITIONS.get(current, [])


def transition_commitment(
    db: Session,
    commitment: Commitment,
    new_status: CommitmentStatus,
    event_data: Optional[dict] = None,
    due_date: Optional[datetime] = None,
) -> bool:
    """
    Transition a commitment to a new status.
    Creates a CommitmentEvent for the timeline.
    Returns True if transition happened, False if invalid.
    """
    current_status = CommitmentStatus(commitment.status)

    if not can_transition(current_status, new_status):
        print(
            f"[StateMachine] Invalid transition: "
            f"{current_status} → {new_status} for commitment {commitment.id}"
        )
        return False

    old_status = commitment.status
    commitment.status = new_status
    commitment.updated_at = datetime.now(timezone.utc)

    if due_date is not None:
        commitment.due_date = due_date

    # Build event data
    evt_data = {
        "from_status": str(old_status),
        "to_status": str(new_status),
    }
    if event_data:
        evt_data.update(event_data)

    event = CommitmentEvent(
        commitment_id=commitment.id,
        event_type=new_status.value,
        event_data=evt_data,
    )
    db.add(event)
    return True


def mark_missed_if_overdue(db: Session) -> int:
    """
    Scan all active commitments.
    If due_date has passed and no fulfillment evidence → mark as missed.

    CRITICAL: Only marks missed if due_date is set and clearly past.
    Never marks fulfilled commitments as missed.
    Returns count of commitments marked missed.
    """
    now = datetime.now(timezone.utc)

    active_statuses = [
        CommitmentStatus.ACTIVE,
        CommitmentStatus.CONFIRMED,
        CommitmentStatus.DETECTED,
        CommitmentStatus.MODIFIED,
    ]

    overdue = (
        db.query(Commitment)
        .filter(
            Commitment.status.in_(active_statuses),
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
            event_data={"reason": "due_date_passed", "checked_at": now.isoformat()},
        )
        if success:
            count += 1

    if count > 0:
        db.commit()

    return count