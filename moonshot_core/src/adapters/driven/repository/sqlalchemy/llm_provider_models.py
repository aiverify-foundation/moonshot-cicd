"""SQLAlchemy ORM models for database tables."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class LLMProviderModel(Base):
    """
    SQLAlchemy model for the llm_provider table.
    
    This model represents an LLM provider in the database.
    """
    __tablename__ = "llm_provider"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    def __repr__(self) -> str:
        return f"<LLMProviderModel(id={self.id}, name='{self.name}')>"

