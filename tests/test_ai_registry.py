# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the AI System Registry service."""

from __future__ import annotations

import pytest

from app.services.ai_registry import (
    AISystem,
    AISystemCreate,
    AISystemRiskLevel,
    AISystemStatus,
    AISystemType,
    AISystemUpdate,
    classify_risk_level,
    delete_ai_system,
    detect_shadow_ai,
    get_ai_system,
    get_dependency_map,
    get_registry_dashboard,
    list_ai_systems,
    register_ai_system,
    reset_registry,
    update_ai_system,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_registry()
    yield
    reset_registry()


ORG_ID = "org-test-001"


def _create_system(
    name: str = "テストAIシステム",
    ai_type: AISystemType = AISystemType.GENERATIVE,
    department: str = "IT部門",
    owner: str = "田中太郎",
    risk_level: AISystemRiskLevel | None = None,
    data_types: list[str] | None = None,
    purpose: str = "社内チャットボット",
    it_approved: bool = True,
    deployment_date: str = "2026-01-01",
    description: str = "社内問い合わせ対応AI",
    status: AISystemStatus = AISystemStatus.ACTIVE,
    dependencies: list[str] | None = None,
) -> AISystem:
    return register_ai_system(AISystemCreate(
        organization_id=ORG_ID,
        name=name,
        description=description,
        ai_type=ai_type,
        department=department,
        owner=owner,
        risk_level=risk_level,
        data_types=data_types or [],
        purpose=purpose,
        it_approved=it_approved,
        deployment_date=deployment_date,
        status=status,
        dependencies=dependencies or [],
    ))


# ── CRUD Tests ──────────────────────────────────────────────────

class TestCRUD:
    def test_register_and_get(self):
        system = _create_system()
        assert system.id
        assert system.name == "テストAIシステム"
        assert system.organization_id == ORG_ID

        fetched = get_ai_system(system.id)
        assert fetched is not None
        assert fetched.name == system.name

    def test_get_nonexistent(self):
        assert get_ai_system("nonexistent") is None

    def test_update(self):
        system = _create_system()
        updated = update_ai_system(system.id, AISystemUpdate(
            name="更新済みシステム",
            department="マーケティング部門",
        ))
        assert updated is not None
        assert updated.name == "更新済みシステム"
        assert updated.department == "マーケティング部門"

    def test_update_nonexistent(self):
        assert update_ai_system("nonexistent", AISystemUpdate(name="x")) is None

    def test_delete(self):
        system = _create_system()
        assert delete_ai_system(system.id) is True
        assert get_ai_system(system.id) is None

    def test_delete_nonexistent(self):
        assert delete_ai_system("nonexistent") is False

    def test_list_systems(self):
        _create_system(name="System A")
        _create_system(name="System B", department="営業部門")
        _create_system(name="System C", status=AISystemStatus.RETIRED)

        all_systems = list_ai_systems(ORG_ID)
        assert len(all_systems) == 3

    def test_list_filter_status(self):
        _create_system(name="Active", status=AISystemStatus.ACTIVE)
        _create_system(name="Retired", status=AISystemStatus.RETIRED)

        active = list_ai_systems(ORG_ID, status=AISystemStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "Active"

    def test_list_filter_risk(self):
        _create_system(name="High Risk", risk_level=AISystemRiskLevel.HIGH)
        _create_system(name="Low Risk", risk_level=AISystemRiskLevel.MINIMAL)

        high = list_ai_systems(ORG_ID, risk_level=AISystemRiskLevel.HIGH)
        assert len(high) == 1
        assert high[0].name == "High Risk"

    def test_list_filter_department(self):
        _create_system(name="IT System", department="IT")
        _create_system(name="HR System", department="HR")

        it_systems = list_ai_systems(ORG_ID, department="IT")
        assert len(it_systems) == 1

    def test_list_other_org(self):
        _create_system()
        assert list_ai_systems("other-org") == []


# ── Risk Classification Tests ───────────────────────────────────

class TestRiskClassification:
    def test_high_risk_biometric(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="顔認証入退室管理",
            description="生体認証によるアクセス制御",
            ai_type=AISystemType.CLASSIFICATION,
        )
        assert classify_risk_level(data) == AISystemRiskLevel.HIGH

    def test_high_risk_healthcare(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="AI診断支援",
            description="医療画像の診断補助",
            ai_type=AISystemType.PREDICTIVE,
        )
        assert classify_risk_level(data) == AISystemRiskLevel.HIGH

    def test_high_risk_employment(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="採用スクリーニング",
            description="履歴書の自動スクリーニング",
            ai_type=AISystemType.CLASSIFICATION,
        )
        assert classify_risk_level(data) == AISystemRiskLevel.HIGH

    def test_high_risk_personal_predictive(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="Customer Predictor",
            description="User behavior model",
            ai_type=AISystemType.PREDICTIVE,
            data_types=["personal"],
        )
        assert classify_risk_level(data) == AISystemRiskLevel.HIGH

    def test_limited_risk_chatbot(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="社内チャットボット",
            description="FAQ応答",
            ai_type=AISystemType.OTHER,
        )
        assert classify_risk_level(data) == AISystemRiskLevel.LIMITED

    def test_limited_risk_generative(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="文書生成AI",
            description="レポート作成支援",
            ai_type=AISystemType.GENERATIVE,
        )
        assert classify_risk_level(data) == AISystemRiskLevel.LIMITED

    def test_minimal_risk(self):
        data = AISystemCreate(
            organization_id=ORG_ID,
            name="在庫最適化",
            description="在庫レベルの最適化",
            ai_type=AISystemType.RECOMMENDATION,
        )
        assert classify_risk_level(data) == AISystemRiskLevel.MINIMAL

    def test_auto_classification_on_register(self):
        system = register_ai_system(AISystemCreate(
            organization_id=ORG_ID,
            name="採用AI",
            description="新卒採用のスクリーニング",
            ai_type=AISystemType.CLASSIFICATION,
        ))
        assert system.risk_level == AISystemRiskLevel.HIGH

    def test_manual_classification_override(self):
        system = _create_system(
            name="Simple Tool",
            risk_level=AISystemRiskLevel.HIGH,
            ai_type=AISystemType.OTHER,
        )
        assert system.risk_level == AISystemRiskLevel.HIGH


# ── Governance Score Tests ──────────────────────────────────────

class TestGovernanceScore:
    def test_full_governance_score(self):
        system = _create_system(
            owner="田中太郎",
            department="IT",
            description="テスト",
            purpose="テスト用途",
            deployment_date="2026-01-01",
            it_approved=True,
        )
        assert system.governance_score > 0.8

    def test_low_governance_score(self):
        system = _create_system(
            owner="",
            department="",
            description="",
            purpose="",
            deployment_date="",
            it_approved=False,
        )
        assert system.governance_score < 0.5

    def test_governance_score_updates_on_update(self):
        system = _create_system(owner="", department="", purpose="")
        score_before = system.governance_score

        updated = update_ai_system(system.id, AISystemUpdate(
            owner="新オーナー",
            department="IT部門",
            purpose="テスト用途",
        ))
        assert updated is not None
        assert updated.governance_score > score_before


# ── Shadow AI Detection Tests ───────────────────────────────────

class TestShadowAI:
    def test_detect_shadow_ai(self):
        _create_system(name="Approved AI", it_approved=True)
        _create_system(name="Shadow AI 1", it_approved=False)
        _create_system(name="Shadow AI 2", it_approved=False)

        shadows = detect_shadow_ai(ORG_ID)
        assert len(shadows) == 2
        names = {s.name for s in shadows}
        assert "Shadow AI 1" in names
        assert "Shadow AI 2" in names

    def test_no_shadow_ai(self):
        _create_system(it_approved=True)
        assert detect_shadow_ai(ORG_ID) == []


# ── Dependency Map Tests ────────────────────────────────────────

class TestDependencyMap:
    def test_dependency_map(self):
        base = _create_system(name="Base AI")
        dependent = _create_system(name="Dependent AI", dependencies=[base.id])

        dep_map = get_dependency_map(dependent.id)
        assert dep_map is not None
        assert len(dep_map.depends_on) == 1
        assert dep_map.depends_on[0]["name"] == "Base AI"

        base_map = get_dependency_map(base.id)
        assert base_map is not None
        assert len(base_map.depended_by) == 1
        assert base_map.depended_by[0]["name"] == "Dependent AI"

    def test_dependency_map_nonexistent(self):
        assert get_dependency_map("nonexistent") is None

    def test_no_dependencies(self):
        system = _create_system()
        dep_map = get_dependency_map(system.id)
        assert dep_map is not None
        assert dep_map.depends_on == []
        assert dep_map.depended_by == []


# ── Dashboard Tests ─────────────────────────────────────────────

class TestDashboard:
    def test_dashboard(self):
        _create_system(name="A", risk_level=AISystemRiskLevel.HIGH, department="IT")
        _create_system(name="B", risk_level=AISystemRiskLevel.MINIMAL, department="HR")
        _create_system(name="C", status=AISystemStatus.UNDER_REVIEW, department="IT")
        _create_system(name="D", it_approved=False)

        dashboard = get_registry_dashboard(ORG_ID)
        assert dashboard.total_systems == 4
        assert dashboard.by_risk_level.get("high", 0) == 1
        assert dashboard.by_department.get("IT", 0) == 2
        assert dashboard.under_review_count == 1
        assert dashboard.shadow_ai_count == 1
        assert dashboard.avg_governance_score > 0

    def test_empty_dashboard(self):
        dashboard = get_registry_dashboard(ORG_ID)
        assert dashboard.total_systems == 0
        assert dashboard.avg_governance_score == 0.0
