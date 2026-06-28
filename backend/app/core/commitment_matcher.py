"""
Commitment Matcher.

Determines whether an incoming commitment is:
A) A brand new commitment
B) An update to an existing commitment (deadline change, owner change)

Uses fuzzy text similarity to match actions.
"""
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from app.models.commitment import Commitment
from app.models.enums import CommitmentStatus

SIMILARITY_THRESHOLD = 0.65


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_matching_commitment(
    db: Session,
    owner: str,
    action: str,
    source_transcript_id: int,
) -> Optional[Commitment]:
    """
    Try to find existing open commitment matching owner + action.
    NEVER matches fulfilled or cancelled commitments.
    NEVER matches commitments from same transcript.
    """
    # Only match genuinely open commitments — never terminal states
    open_statuses = [
        CommitmentStatus.DETECTED,
        CommitmentStatus.CONFIRMED,
        CommitmentStatus.ACTIVE,
        CommitmentStatus.MODIFIED,
        CommitmentStatus.BLOCKED,
    ]

    existing = (
        db.query(Commitment)
        .filter(
            Commitment.status.in_(open_statuses),
            Commitment.source_transcript_id != source_transcript_id,
        )
        .all()
    )

    best_match = None
    best_score = 0.0

    for commitment in existing:
        # Owner must match exactly
        if commitment.owner.lower().strip() != owner.lower().strip():
            continue

        action_score = _similarity(commitment.action, action)
        if action_score > best_score and action_score >= SIMILARITY_THRESHOLD:
            best_score = action_score
            best_match = commitment

    return best_match


def is_fulfillment_evidence(
    commitment_action: str,
    new_text: str,
) -> bool:
    """
    Check if new_text is evidence that commitment_action was fulfilled.
    Conservative — prefers false negative over false positive.
    (False Failure Rate must stay < 1%)
    """
    action_lower = commitment_action.lower()
    text_lower = new_text.lower()

    # Very high similarity = same action repeated = NOT fulfillment
    # (fulfillment evidence usually sounds different)
    direct_similarity = _similarity(action_lower, text_lower)
    if direct_similarity > 0.85:
        return False  # too similar = just a repeated commitment, not evidence

    # Fulfillment signal words
    fulfillment_signals = [
        "sent", "done", "completed", "finished", "delivered",
        "submitted", "reviewed", "called", "updated", "shared",
        "uploaded", "published", "fixed", "resolved", "closed",
        "approved", "has been", "have been", "already",
        "it's done", "its done", "all done",
    ]

    # Key words from original action
    action_keywords = [
        word for word in action_lower.split()
        if len(word) > 3 and word not in {
            "will", "shall", "going", "need", "have",
            "that", "this", "with", "from", "the", "and",
        }
    ]

    has_signal = any(s in text_lower for s in fulfillment_signals)
    has_keyword = any(kw in text_lower for kw in action_keywords)

    # Both must be present for fulfillment
    return has_signal and has_keyword