from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class CommitmentEvent(Base):
    __tablename__ = "commitment_events"

    id = Column(Integer, primary_key=True, index=True)
    commitment_id = Column(Integer, ForeignKey("commitments.id"), nullable=False)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    commitment = relationship("Commitment", back_populates="events")
