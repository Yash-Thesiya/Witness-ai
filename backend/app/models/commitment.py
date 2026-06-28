from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import CommitmentStatus


class Commitment(Base):
    __tablename__ = "commitments"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    action = Column(String, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(CommitmentStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=CommitmentStatus.DETECTED)
    confidence_score = Column(Float, nullable=True)
    source_transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    source_transcript = relationship("Transcript", back_populates="commitments")
    events = relationship("CommitmentEvent", back_populates="commitment", cascade="all, delete-orphan")
