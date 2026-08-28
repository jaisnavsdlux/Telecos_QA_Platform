"""
SQLAlchemy Data Models for Users, Projects, Runs, Verdicts, and Token Usage.
Compatible with Neon PostgreSQL and SQLite.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(150), default="")
    email = Column(String(200), default="")
    role = Column(String(50), default="engineer")
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    structure_type = Column(String(100), default="CONCRETE MONOPOLE (26.8m)")
    drawing_revision = Column(String(100), default="FOR CONSTRUCTION (Rev 1.0)")
    primary_drawing = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String(100), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("projects.id"), index=True, nullable=False)
    status = Column(String(50), default="completed")
    model = Column(String(100), default="gemma4:cloud")
    elapsed_seconds = Column(Float, default=0.0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    unclear_count = Column(Integer, default=0)
    na_count = Column(Integer, default=0)
    total_rules = Column(Integer, default=71)
    report_filename = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    verdicts = relationship("RuleVerdict", back_populates="run", cascade="all, delete-orphan")

class RuleVerdict(Base):
    __tablename__ = "rule_verdicts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(100), ForeignKey("validation_runs.id"), index=True, nullable=False)
    rule_code = Column(String(50), index=True, nullable=False)
    verdict = Column(String(50), nullable=False)  # PASS, FAIL, UNCLEAR, NOT_APPLICABLE
    confidence = Column(Float, default=1.0)
    reasoning = Column(Text, default="")
    evidence_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ValidationRun", back_populates="verdicts")

class TokenUsageLog(Base):
    __tablename__ = "token_usage_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String(50), index=True, nullable=False)
    model = Column(String(100), default="gemma4:cloud")
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    cache_creation_tokens = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
