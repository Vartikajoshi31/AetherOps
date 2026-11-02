import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class BaseModelMixin:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self):
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if isinstance(val, datetime):
                result[c.name] = val.isoformat()
            else:
                result[c.name] = val
        return result
