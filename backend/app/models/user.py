from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import BaseModelMixin

class Organization(Base, BaseModelMixin):
    __tablename__ = "organizations"

    name = Column(String(128), nullable=False, unique=True)
    slug = Column(String(64), nullable=False, unique=True, index=True)
    plan = Column(String(32), default="enterprise")

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="organization", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="organization", cascade="all, delete-orphan")

class User(Base, BaseModelMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), default="engineer")  # admin, engineer, viewer
    is_active = Column(Boolean, default=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    organization = relationship("Organization", back_populates="users")
    approvals = relationship("Approval", back_populates="reviewer")
