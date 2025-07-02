"""SQLAlchemy models for Vulkan Agent storage."""

import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class MessageRole(str, Enum):
    """Valid message roles for conversation."""

    USER = "user"
    ASSISTANT = "assistant"


class AgentConfig(Base):
    """Single agent configuration table."""

    __tablename__ = "agent_config"

    id = Column(Integer, primary_key=True)
    provider = Column(String(20), nullable=False)
    api_key = Column(Text, nullable=False)
    model = Column(String(50), nullable=False)
    max_tokens = Column(Integer, default=500)
    temperature = Column(Float, default=0.7)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Session(Base):
    """Conversation sessions."""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to messages
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    """Individual messages in conversations."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    role = Column(String(10), nullable=False)  # MessageRole: 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to session
    session = relationship("Session", back_populates="messages")
