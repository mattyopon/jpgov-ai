# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""SQLite database layer for JPGovAI prototype."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


# ── ORM Models ────────────────────────────────────────────────────

class OrganizationRow(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    industry = Column(String, default="")
    size = Column(String, default="")
    ai_role = Column(String, default="")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class AssessmentRow(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    answers_json = Column(Text, default="{}")
    overall_score = Column(Float, default=0.0)
    maturity_level = Column(Integer, default=1)
    category_scores_json = Column(Text, default="[]")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class GapAnalysisRow(Base):
    __tablename__ = "gap_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    assessment_id = Column(String, nullable=False)
    result_json = Column(Text, default="{}")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class EvidenceRow(Base):
    __tablename__ = "evidences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    requirement_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    description = Column(String, default="")
    file_type = Column(String, default="")
    file_path = Column(String, default="")
    uploaded_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class ReportRow(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    assessment_id = Column(String, default="")
    gap_analysis_id = Column(String, default="")
    filename = Column(String, default="")
    content_json = Column(Text, default="{}")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class AuditEventRow(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    payload_json = Column(Text, default="{}")
    payload_hash = Column(String, default="")
    previous_hash = Column(String, default="")
    event_hash = Column(String, default="")


class RiskAssessmentRow(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    system_name = Column(String, default="")
    result_json = Column(Text, default="{}")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class ActionTaskRow(Base):
    __tablename__ = "action_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    result_json = Column(Text, default="{}")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class OrganizationMemberRow(Base):
    __tablename__ = "organization_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    email = Column(String, default="")
    display_name = Column(String, default="")
    role = Column(String, default="member")
    invited_by = Column(String, default="")
    joined_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class AssessmentSnapshotRow(Base):
    __tablename__ = "assessment_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    assessment_id = Column(String, nullable=False)
    overall_score = Column(Float, default=0.0)
    maturity_level = Column(Integer, default=1)
    category_scores_json = Column(Text, default="{}")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class ReviewCycleRow(Base):
    __tablename__ = "review_cycles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    cycle_type = Column(String, default="quarterly")
    start_date = Column(String, default="")
    next_review_date = Column(String, default="")
    created_by = Column(String, default="")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class ReviewRecordRow(Base):
    __tablename__ = "review_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    cycle_id = Column(String, nullable=False)
    review_date = Column(String, default="")
    assessment_id = Column(String, default="")
    reviewer = Column(String, default="")
    notes = Column(Text, default="")
    delta_report_json = Column(Text, default="{}")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class BenchmarkDataRow(Base):
    __tablename__ = "benchmark_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    size_bucket = Column(String, default="")
    overall_score = Column(Float, default=0.0)
    maturity_level = Column(Integer, default=1)
    category_scores_json = Column(Text, default="{}")
    opt_in = Column(Integer, default=1)  # 1=opted in, 0=opted out
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalRequestRow(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    request_type = Column(String, default="")
    title = Column(String, default="")
    description = Column(Text, default="")
    resource_type = Column(String, default="")
    resource_id = Column(String, default="")
    requested_by = Column(String, default="")
    approver_id = Column(String, default="")
    status = Column(String, default="pending")
    comment = Column(Text, default="")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class IncidentRow(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    incident_type = Column(String, default="other")
    severity = Column(String, default="medium")
    affected_system = Column(String, default="")
    impact_description = Column(Text, default="")
    status = Column(String, default="open")
    detected_by = Column(String, default="")
    detected_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at = Column(String, default="")
    related_requirements_json = Column(Text, default="[]")
    regulatory_report_required = Column(Integer, default=0)
    regulatory_report_sent = Column(Integer, default=0)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class IncidentRCARow(Base):
    __tablename__ = "incident_rcas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, nullable=False)
    root_cause = Column(Text, default="")
    contributing_factors_json = Column(Text, default="[]")
    corrective_actions_json = Column(Text, default="[]")
    preventive_actions_json = Column(Text, default="[]")
    lessons_learned = Column(Text, default="")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class IntegrationConfigRow(Base):
    __tablename__ = "integration_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    integration_type = Column(String, default="slack")
    webhook_url = Column(String, default="")
    enabled = Column(Integer, default=1)
    notify_review_reminder = Column(Integer, default=1)
    notify_approval = Column(Integer, default=1)
    notify_incident = Column(Integer, default=1)
    notify_score_drop = Column(Integer, default=1)
    notify_new_gap = Column(Integer, default=1)
    language = Column(String, default="ja")
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


class MonthlyReportRow(Base):
    __tablename__ = "monthly_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    report_json = Column(Text, default="{}")
    generated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())


# ── Database Manager ──────────────────────────────────────────────

class DatabaseManager:
    """Simple SQLite database manager."""

    def __init__(self, db_url: str = "sqlite:///./jpgov_ai.db") -> None:
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all tables."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()


# Singleton
_db: DatabaseManager | None = None


def get_db(db_url: str = "sqlite:///./jpgov_ai.db") -> DatabaseManager:
    """Get or create the database manager singleton."""
    global _db
    if _db is None:
        _db = DatabaseManager(db_url)
        _db.create_tables()
    return _db


def reset_db() -> None:
    """Reset the singleton (for testing)."""
    global _db
    _db = None
