# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for audit package service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.services.assessment import run_assessment
from app.services.audit_package import (
    generate_corrective_action_template,
    generate_internal_audit_checklist,
    generate_iso42001_stage1_package,
    generate_management_review_template,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


def _create_assessment() -> tuple[str, str]:
    """Create a test assessment and gap analysis."""
    from app.models import AnswerItem
    answers = [
        AnswerItem(question_id=f"Q{i:02d}", selected_index=2)
        for i in range(1, 26)
    ]
    result = run_assessment("org-test", answers)

    # Run gap analysis
    from app.services.gap_analysis import run_gap_analysis
    import asyncio
    gap = asyncio.get_event_loop().run_until_complete(run_gap_analysis(result))
    return result.id, gap.id


class TestAuditPackage:
    """監査パッケージのテスト."""

    def test_generate_iso_stage1_package(self):
        """ISO Stage 1パッケージが生成されること."""
        _, gap_id = _create_assessment()
        package = generate_iso42001_stage1_package(
            organization_id="org-test",
            gap_analysis_id=gap_id,
            organization_name="テスト株式会社",
        )

        assert package.audit_type == "iso42001_stage1"
        assert package.organization_id == "org-test"
        assert len(package.documents) >= 5
        assert "01_aims_scope.md" in package.documents
        assert "02_ai_policy.md" in package.documents
        assert "06_internal_audit_checklist.md" in package.documents

    def test_package_has_sections(self):
        """パッケージにセクションがあること."""
        _, gap_id = _create_assessment()
        package = generate_iso42001_stage1_package(
            organization_id="org-test",
            gap_analysis_id=gap_id,
        )

        assert len(package.sections) > 0
        for section in package.sections:
            assert section.requirement_id
            assert section.requirement_title
            assert section.compliance_status

    def test_package_to_dict(self):
        """パッケージが辞書に変換できること."""
        _, gap_id = _create_assessment()
        package = generate_iso42001_stage1_package(
            organization_id="org-test",
            gap_analysis_id=gap_id,
        )

        data = package.to_dict()
        assert "id" in data
        assert "sections" in data
        assert "document_count" in data
        assert data["document_count"] >= 5

    def test_internal_audit_checklist(self):
        """内部監査チェックリストが生成されること."""
        result = generate_internal_audit_checklist()
        assert "internal_audit_checklist.md" in result
        content = result["internal_audit_checklist.md"]
        assert "チェック項目" in content
        assert "リーダーシップ" in content
        assert "パフォーマンス評価" in content

    def test_management_review_template(self):
        """マネジメントレビュー議事録が生成されること."""
        result = generate_management_review_template("テスト株式会社")
        assert "management_review_template.md" in result
        content = result["management_review_template.md"]
        assert "テスト株式会社" in content
        assert "インプット" in content
        assert "アウトプット" in content

    def test_corrective_action_template(self):
        """是正措置テンプレートが生成されること."""
        result = generate_corrective_action_template()
        assert "corrective_action_template.md" in result
        content = result["corrective_action_template.md"]
        assert "原因分析" in content
        assert "是正措置" in content
        assert "有効性確認" in content

    def test_aims_scope_content(self):
        """AIMS適用範囲の内容が正しいこと."""
        _, gap_id = _create_assessment()
        package = generate_iso42001_stage1_package(
            organization_id="org-test",
            gap_analysis_id=gap_id,
            organization_name="ABC株式会社",
        )

        scope_doc = package.documents.get("01_aims_scope.md", "")
        assert "ABC株式会社" in scope_doc
        assert "適用範囲" in scope_doc

    def test_risk_assessment_summary(self):
        """リスクアセスメントサマリーが生成されること."""
        _, gap_id = _create_assessment()
        package = generate_iso42001_stage1_package(
            organization_id="org-test",
            gap_analysis_id=gap_id,
        )

        assert "03_risk_assessment_summary.md" in package.documents
        content = package.documents["03_risk_assessment_summary.md"]
        assert "概要" in content
        assert "要件別評価結果" in content
