"""SQLAlchemy models for data persistence."""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AnalysisResult(Base):
    """Model for storing analysis results."""
    
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True)
    analysis_type = Column(String(50), nullable=False)
    database_name = Column(String(255))
    database_type = Column(String(20))  # oracle or mssql
    status = Column(String(20))
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)  # Additional metadata


class ConnectionProfile(Base):
    """Model for storing connection profiles."""
    
    __tablename__ = "connection_profiles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    db_type = Column(String(20))
    host = Column(String(255))
    port = Column(Integer)
    service = Column(String(255))
    username = Column(String(255))
    # Password stored encrypted
    password_encrypted = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)

