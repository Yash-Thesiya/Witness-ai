import enum


class CommitmentStatus(str, enum.Enum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    MODIFIED = "modified"
    BLOCKED = "blocked"
    FULFILLED = "fulfilled"
    MISSED = "missed"
    CANCELLED = "cancelled"


class FileType(str, enum.Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
