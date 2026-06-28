"""
Commitments router.
GET    /commitments/              - list with search/filter
GET    /commitments/{id}          - detail with timeline
PATCH  /commitments/{id}/status   - manually update status
GET    /commitments/dashboard     - dashboard stats
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.state_machine import transition_commitment
from app.db.database import get_db
from app.models.commitment import Commitment
from app.models.enums import CommitmentStatus
from app.models.transcript import Transcript
from app.models.upload import Upload
from app.models.user import User
from app.schemas.commitment import (
    CommitmentDetailResponse,
    CommitmentListItem,
    CommitmentStatusUpdate,
    DashboardResponse,
)

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard stats — active, fulfilled, missed, due soon."""
    base = (
        db.query(Commitment)
        .join(Transcript, Commitment.source_transcript_id == Transcript.id)
        .join(Upload, Transcript.upload_id == Upload.id)
        .filter(Upload.user_id == current_user.id)
    )

    now = datetime.now(timezone.utc)
    soon = datetime.now(timezone.utc).replace(hour=23, minute=59)
    from datetime import timedelta
    soon = now + timedelta(days=7)

    active = base.filter(Commitment.status == CommitmentStatus.ACTIVE).count()
    fulfilled = base.filter(Commitment.status == CommitmentStatus.FULFILLED).count()
    missed = base.filter(Commitment.status == CommitmentStatus.MISSED).count()
    detected = base.filter(Commitment.status == CommitmentStatus.DETECTED).count()
    due_soon = base.filter(
        Commitment.due_date.isnot(None),
        Commitment.due_date <= soon,
        Commitment.status.in_([
            CommitmentStatus.ACTIVE,
            CommitmentStatus.DETECTED,
            CommitmentStatus.CONFIRMED,
        ]),
    ).count()

    return DashboardResponse(
        active=active,
        fulfilled=fulfilled,
        missed=missed,
        detected=detected,
        due_soon=due_soon,
        total=active + fulfilled + missed + detected,
    )

@router.get("/report/accountability")
def accountability_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accountability report — per owner breakdown.
    Shows: total, active, fulfilled, missed, fulfillment rate.
    """
    from sqlalchemy import func

    all_commitments = (
        db.query(Commitment)
        .join(Transcript, Commitment.source_transcript_id == Transcript.id)
        .join(Upload, Transcript.upload_id == Upload.id)
        .filter(Upload.user_id == current_user.id)
        .all()
    )

    # Group by owner
    owner_stats = {}
    for c in all_commitments:
        owner = c.owner
        if owner not in owner_stats:
            owner_stats[owner] = {
                "owner": owner,
                "total": 0,
                "active": 0,
                "detected": 0,
                "fulfilled": 0,
                "missed": 0,
                "modified": 0,
                "cancelled": 0,
                "blocked": 0,
                "fulfillment_rate": 0.0,
            }

        owner_stats[owner]["total"] += 1
        status = c.status.value if hasattr(c.status, 'value') else str(c.status)
        if status in owner_stats[owner]:
            owner_stats[owner][status] += 1

    # Calculate fulfillment rate per owner
    for owner, stats in owner_stats.items():
        completed = stats["fulfilled"]
        total_closed = stats["fulfilled"] + stats["missed"] + stats["cancelled"]
        if total_closed > 0:
            stats["fulfillment_rate"] = round((completed / total_closed) * 100, 1)
        else:
            stats["fulfillment_rate"] = 0.0

    # Sort by total commitments
    report = sorted(owner_stats.values(), key=lambda x: x["total"], reverse=True)

    return {
        "report": report,
        "summary": {
            "total_owners": len(report),
            "total_commitments": len(all_commitments),
            "overall_fulfilled": sum(r["fulfilled"] for r in report),
            "overall_missed": sum(r["missed"] for r in report),
            "overall_active": sum(r["active"] for r in report),
        }
    }


@router.get("/", response_model=list[CommitmentListItem])
def list_commitments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List commitments with optional filters."""
    query = (
        db.query(Commitment)
        .join(Transcript, Commitment.source_transcript_id == Transcript.id)
        .join(Upload, Transcript.upload_id == Upload.id)
        .filter(Upload.user_id == current_user.id)
    )

    if status:
        try:
            query = query.filter(Commitment.status == CommitmentStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if owner:
        query = query.filter(Commitment.owner.ilike(f"%{owner}%"))

    if search:
        query = query.filter(Commitment.action.ilike(f"%{search}%"))

    return query.order_by(Commitment.created_at.desc()).all()


@router.get("/{commitment_id}", response_model=CommitmentDetailResponse)
def get_commitment(
    commitment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get commitment detail with full timeline."""
    commitment = (
        db.query(Commitment)
        .join(Transcript, Commitment.source_transcript_id == Transcript.id)
        .join(Upload, Transcript.upload_id == Upload.id)
        .filter(
            Commitment.id == commitment_id,
            Upload.user_id == current_user.id,
        )
        .first()
    )
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    return commitment


@router.patch("/{commitment_id}/status")
def update_commitment_status(
    commitment_id: int,
    payload: CommitmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually update commitment status (e.g. mark as fulfilled or cancelled)."""
    commitment = (
        db.query(Commitment)
        .join(Transcript, Commitment.source_transcript_id == Transcript.id)
        .join(Upload, Transcript.upload_id == Upload.id)
        .filter(
            Commitment.id == commitment_id,
            Upload.user_id == current_user.id,
        )
        .first()
    )
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found.")

    try:
        new_status = CommitmentStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")

    success = transition_commitment(
        db,
        commitment,
        new_status,
        event_data={"updated_by": "user_manual", "note": payload.note},
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {commitment.status} to {payload.status}.",
        )

    db.commit()
    return {"message": f"Status updated to {new_status.value}", "commitment_id": commitment_id}