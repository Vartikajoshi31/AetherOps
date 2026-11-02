import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database.session import Base

class BaseModelMixin:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if isinstance(val, datetime):
                result[c.name] = val.isoformat()
            else:
                result[c.name] = val
        return result
