"""
Modelo de usuarios (estudiantes).

TODO (Sprint 0): Completar columnas y constraints.
Incluir: id (UUID PK), email (UNIQUE NOT NULL), password_hash,
nombre, apellido, created_at, updated_at.
Se usará werkzeug.security para hashear contraseñas.
"""

from datetime import datetime
from config.database import Base
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=True)
    apellido = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
