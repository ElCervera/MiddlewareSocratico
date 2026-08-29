"""
Modelo de auditoría de guardrails anti-código.

TODO (Sprint 0): Añadir FK y campos de auditoría.
Incluir: id (PK), message_id (FK → messages.id), codigo_detectado (BOOLEAN),
intento_numero, respuesta_original (TEXT), created_at.
"""

from datetime import datetime
from config.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid


class GuardrailsLog(Base):
    __tablename__ = "guardrails_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    codigo_detectado = Column(Boolean, nullable=False, default=False)
    intento_numero = Column(Integer, nullable=False, default=0)
    respuesta_original = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    message = relationship("Message", back_populates="guardrails_logs")
