from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    audio_path = Column(String, nullable=False)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    upload = relationship("Upload", back_populates="recording")
