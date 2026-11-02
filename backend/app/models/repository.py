from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import BaseModelMixin

class Repository(Base, BaseModelMixin):
    __tablename__ = "repositories"

    name = Column(String(128), nullable=False, index=True)
    full_name = Column(String(255), nullable=False, unique=True, index=True)
    default_branch = Column(String(64), default="main")
    clone_url = Column(String(512), nullable=True)
    local_path = Column(String(512), nullable=True)
    indexed_at = Column(String(64), nullable=True)
    index_status = Column(String(32), default="pending")  # pending, indexing, indexed, failed
    total_files = Column(Integer, default=0)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    organization = relationship("Organization", back_populates="repositories")
    services = relationship("Service", back_populates="repository", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="repository", cascade="all, delete-orphan")

class Service(Base, BaseModelMixin):
    __tablename__ = "services"

    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    tier = Column(String(32), default="critical")  # critical, standard, low
    language = Column(String(64), default="python")
    health_status = Column(String(32), default="healthy")  # healthy, degraded, critical
    current_error_rate = Column(String(32), default="0.00%")
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)
    service_metadata = Column(JSON, default=dict)

    repository = relationship("Repository", back_populates="services")
    deployments = relationship("Deployment", back_populates="service", cascade="all, delete-orphan")
