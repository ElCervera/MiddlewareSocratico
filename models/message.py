"""
Modelo de mensajes dentro de una conversación.

TODO (Sprint 0): Completar campos.
Incluir: id (PK), conversation_id (FK → conversations.id),
role ("human" o "ai"), content (TEXT), tokens_usados,
intentos_refor, created_at, feedback (SMALLINT nullable, 1-5).
"""

from datetime import datetime
from config.database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # "human" o "ai"
    content = Column(Text, nullable=False)
    tokens_usados = Column(Integer, nullable=True)
    intentos_refor = Column(Integer, nullable=False, default=0)
    feedback = Column(SmallInteger, nullable=True)  # 1 a 5 o null
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    guardrails_logs = relationship("GuardrailsLog", back_populates="message", cascade="all, delete-orphan")
