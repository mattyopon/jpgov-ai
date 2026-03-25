# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the enhanced evidence management service (Phase 2)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.db.database import get_db, reset_db
from app.models import EvidenceUpload
from app.services.evidence import (
    get_evidence_coverage_rate,
    get_evidence_summary,
    get_expiring_evidence,
    list_evidence,
    upload_evidence,
    upload_evidence_v2,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path, monkeypatch):
    """Use a temporary database and upload dir for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()

    # Redirect uploads to tmp_path
    upload_dir = tmp_path / "uploads"
    import app.services.evidence as ev_mod
    monkeypatch.setattr(ev_mod, "UPLOAD_DIR", upload_dir)

    yield tmp_path
    reset_db()


def _evidence_upload(
    org_id: str = "org-001",
    req_id: str = "R001",
    filename: str = "test_policy.pdf",
) -> EvidenceUpload:
    return EvidenceUpload(
        organization_id=org_id,
        requirement_id=req_id,
        filename=filename,
        description="テストエビデンス",
        file_type="policy",
    )


class TestUploadEvidence:
    """Evidence upload tests."""

    def test_upload_creates_directory(self, _setup_db):
        """Should create org/req directory structure."""
        tmp = _setup_db
        upload = _evidence_upload()
        record = upload_evidence(upload, file_content=b"hello world")

        assert record.organization_id == "org-001"
        assert record.requirement_id == "R001"
        # Check directory was created
        org_dir = tmp / "uploads" / "org-001" / "R001"
        assert org_dir.exists()

    def test_upload_saves_file(self, _setup_db):
        """Should save file content to disk."""
        content = b"PDF content here"
        upload = _evidence_upload()
        record = upload_evidence(upload, file_content=content)

        file_path = Path(record.file_path)
        assert file_path.exists()
        assert file_path.read_bytes() == content

    def test_upload_metadata_only(self, _setup_db):
        """Should handle metadata-only upload (no file content)."""
        upload = _evidence_upload()
        record = upload_evidence(upload, file_content=None)
        assert record.filename == "test_policy.pdf"
        # File should not exist on disk
        file_path = Path(record.file_path)
        assert not file_path.exists()

    def test_upload_persists_in_db(self, _setup_db):
        """Should persist evidence in database."""
        upload = _evidence_upload()
        upload_evidence(upload, file_content=b"data")

        records = list_evidence("org-001", "R001")
        assert len(records) == 1
        assert records[0].filename == "test_policy.pdf"


class TestUploadEvidenceV2:
    """Enhanced evidence upload tests (v2)."""

    def test_v2_upload_with_metadata(self, _setup_db):
        """Should store enhanced metadata."""
        content = b"Enhanced content"
        upload = _evidence_upload()
        ef = upload_evidence_v2(
            upload,
            file_content=content,
            uploaded_by="user-001",
            expires_at="2027-03-25T00:00:00Z",
        )

        assert ef.file_size == len(content)
        assert ef.file_hash == hashlib.sha256(content).hexdigest()
        assert ef.uploaded_by == "user-001"
        assert ef.expires_at == "2027-03-25T00:00:00Z"

    def test_v2_upload_saves_file(self, _setup_db):
        """Should save file to disk with v2."""
        content = b"test data v2"
        upload = _evidence_upload()
        ef = upload_evidence_v2(upload, file_content=content)

        file_path = Path(ef.file_path)
        assert file_path.exists()
        assert file_path.read_bytes() == content

    def test_v2_upload_no_content(self, _setup_db):
        """Should handle v2 without file content."""
        upload = _evidence_upload()
        ef = upload_evidence_v2(upload, file_content=None)

        assert ef.file_size == 0
        assert ef.file_hash == ""

    def test_v2_backward_compatible(self, _setup_db):
        """Should also persist in the legacy evidence table."""
        upload = _evidence_upload()
        ef = upload_evidence_v2(upload, file_content=b"compat")

        records = list_evidence("org-001", "R001")
        assert len(records) == 1
        assert records[0].id == ef.id


class TestEvidenceSummary:
    """Evidence summary tests."""

    def test_empty_summary(self, _setup_db):
        """Should return zero coverage for org with no evidence."""
        summary = get_evidence_summary("org-001")
        assert summary.coverage_rate == 0.0
        assert summary.requirements_with_evidence == 0

    def test_coverage_with_evidence(self, _setup_db):
        """Should compute coverage rate."""
        # Use actual requirement IDs from the guidelines
        upload_evidence(_evidence_upload(req_id="C01-R01"), file_content=b"a")
        upload_evidence(_evidence_upload(req_id="C01-R02"), file_content=b"b")

        summary = get_evidence_summary("org-001")
        assert summary.requirements_with_evidence >= 2
        assert summary.coverage_rate > 0.0

    def test_coverage_rate_function(self, _setup_db):
        """Should return coverage rate via helper function."""
        rate = get_evidence_coverage_rate("org-001")
        assert rate == 0.0

        upload_evidence(_evidence_upload(req_id="C01-R01"), file_content=b"x")
        rate = get_evidence_coverage_rate("org-001")
        assert rate > 0.0


class TestExpiringEvidence:
    """Evidence expiration tests."""

    def test_expiring_returns_empty(self, _setup_db):
        """Should return empty list (future DB extension)."""
        result = get_expiring_evidence("org-001", within_days=30)
        assert result == []


class TestListEvidence:
    """Evidence listing tests."""

    def test_list_all(self, _setup_db):
        """Should list all evidence for an organization."""
        upload_evidence(_evidence_upload(req_id="R001"), file_content=b"a")
        upload_evidence(_evidence_upload(req_id="R002"), file_content=b"b")

        records = list_evidence("org-001")
        assert len(records) == 2

    def test_list_by_requirement(self, _setup_db):
        """Should filter by requirement ID."""
        upload_evidence(_evidence_upload(req_id="R001"), file_content=b"a")
        upload_evidence(_evidence_upload(req_id="R002"), file_content=b"b")

        records = list_evidence("org-001", "R001")
        assert len(records) == 1
        assert records[0].requirement_id == "R001"

    def test_list_different_orgs(self, _setup_db):
        """Should isolate evidence by organization."""
        upload_evidence(_evidence_upload(org_id="org-001"), file_content=b"a")
        upload_evidence(_evidence_upload(org_id="org-002"), file_content=b"b")

        assert len(list_evidence("org-001")) == 1
        assert len(list_evidence("org-002")) == 1
