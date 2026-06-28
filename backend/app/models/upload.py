from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.models.enums import FileType


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(Enum(FileType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    # pending → processing → completed / failed
    processing_status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="uploads")
    recording = relationship("Recording", back_populates="upload", uselist=False, cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="upload", uselist=False, cascade="all, delete-orphan")
