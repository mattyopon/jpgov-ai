# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""AIシステム台帳管理サービス.

企業が使っている全AIシステムの台帳管理:
- CRUD操作
- EU AI Act準拠のリスク自動分類
- Shadow AI検出
- 依存関係マッピング
- ガバナンススコア算出
- ダッシュボード情報
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────

class AISystemType(str, Enum):
    """AIシステム種別."""

    GENERATIVE = "generative"
    PREDICTIVE = "predictive"
    CLASSIFICATION = "classification"
    RECOMMENDATION = "recommendation"
    OTHER = "other"


class AISystemStatus(str, Enum):
    """AIシステムステータス."""

    ACTIVE = "active"
    RETIRED = "retired"
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"


class AISystemRiskLevel(str, Enum):
    """AIシステムリスクレベル (EU AI Act準拠)."""

    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class DataType(str, Enum):
    """データ種別."""

    PERSONAL = "personal"
    CONFIDENTIAL = "confidential"
    PUBLIC = "public"


# ── Models ───────────────────────────────────────────────────────

class AISystem(BaseModel):
    """AIシステム台帳レコード."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    ai_type: AISystemType = AISystemType.OTHER
    vendor: str = ""
    department: str = ""
    owner: str = ""
    risk_level: AISystemRiskLevel = AISystemRiskLevel.MINIMAL
    status: AISystemStatus = AISystemStatus.ACTIVE
    data_types: list[str] = Field(default_factory=list)
    purpose: str = ""
    deployment_date: str = ""
    organization_id: str = ""
    governance_score: float = 0.0
    dependencies: list[str] = Field(default_factory=list)  # list of AI system IDs
    it_approved: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AISystemCreate(BaseModel):
    """AIシステム登録リクエスト."""

    organization_id: str
    name: str
    description: str = ""
    ai_type: AISystemType = AISystemType.OTHER
    vendor: str = ""
    department: str = ""
    owner: str = ""
    risk_level: AISystemRiskLevel | None = None  # None=自動分類
    status: AISystemStatus = AISystemStatus.ACTIVE
    data_types: list[str] = Field(default_factory=list)
    purpose: str = ""
    deployment_date: str = ""
    dependencies: list[str] = Field(default_factory=list)
    it_approved: bool = True


class AISystemUpdate(BaseModel):
    """AIシステム更新リクエスト."""

    name: str | None = None
    description: str | None = None
    ai_type: AISystemType | None = None
    vendor: str | None = None
    department: str | None = None
    owner: str | None = None
    risk_level: AISystemRiskLevel | None = None
    status: AISystemStatus | None = None
    data_types: list[str] | None = None
    purpose: str | None = None
    deployment_date: str | None = None
    dependencies: list[str] | None = None
    it_approved: bool | None = None


class AIRegistryDashboard(BaseModel):
    """AIシステム台帳ダッシュボード."""

    organization_id: str
    total_systems: int = 0
    by_risk_level: dict[str, int] = Field(default_factory=dict)
    by_department: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    under_review_count: int = 0
    shadow_ai_count: int = 0
    avg_governance_score: float = 0.0


class DependencyMap(BaseModel):
    """AIシステム依存関係マップ."""

    system_id: str
    system_name: str
    depends_on: list[dict[str, str]] = Field(default_factory=list)
    depended_by: list[dict[str, str]] = Field(default_factory=list)


# ── In-memory storage ────────────────────────────────────────────

_ai_systems: dict[str, AISystem] = {}


# ── EU AI Act リスク自動分類 ────────────────────────────────────

# High risk keywords / patterns (EU AI Act Article 6 & Annex III)
_HIGH_RISK_KEYWORDS = [
    "biometric", "生体", "顔認証", "face recognition",
    "critical infrastructure", "重要インフラ", "インフラ",
    "education", "教育", "入試", "entrance exam",
    "employment", "雇用", "採用", "recruitment", "hr",
    "credit scoring", "信用スコア", "融資審査", "loan",
    "law enforcement", "法執行", "犯罪", "crime",
    "healthcare", "医療", "診断", "diagnosis",
    "safety", "安全", "自動運転", "autonomous",
]

_LIMITED_RISK_KEYWORDS = [
    "chatbot", "チャットボット", "chat",
    "content generation", "コンテンツ生成", "生成AI",
    "deepfake", "ディープフェイク",
    "emotion recognition", "感情認識",
    "generative", "生成",
]


def classify_risk_level(system: AISystemCreate) -> AISystemRiskLevel:
    """EU AI Act準拠のリスク自動分類.

    AIシステムの説明、用途、データ種別からリスクレベルを推定する。

    Args:
        system: AIシステム登録情報

    Returns:
        AISystemRiskLevel: 推定されたリスクレベル
    """
    text = f"{system.name} {system.description} {system.purpose}".lower()

    # 個人データを扱う場合はリスクが上がる
    has_personal_data = "personal" in system.data_types

    # High risk check
    for keyword in _HIGH_RISK_KEYWORDS:
        if keyword.lower() in text:
            return AISystemRiskLevel.HIGH

    if has_personal_data and system.ai_type in (
        AISystemType.CLASSIFICATION,
        AISystemType.PREDICTIVE,
    ):
        return AISystemRiskLevel.HIGH

    # Limited risk check
    for keyword in _LIMITED_RISK_KEYWORDS:
        if keyword.lower() in text:
            return AISystemRiskLevel.LIMITED

    if system.ai_type == AISystemType.GENERATIVE:
        return AISystemRiskLevel.LIMITED

    return AISystemRiskLevel.MINIMAL


# ── ガバナンススコア算出 ────────────────────────────────────────

def _calculate_governance_score(system: AISystem) -> float:
    """AIシステムのガバナンススコアを算出.

    以下の基準で0.0〜1.0のスコアを付与:
    - オーナーが設定されている
    - 部門が設定されている
    - 説明が記載されている
    - 目的が記載されている
    - リスクレベルが評価済み
    - IT承認済み
    - デプロイ日が記録されている

    Args:
        system: AIシステム

    Returns:
        float: ガバナンススコア (0.0-1.0)
    """
    checks = [
        bool(system.owner),
        bool(system.department),
        bool(system.description),
        bool(system.purpose),
        system.risk_level != AISystemRiskLevel.MINIMAL or bool(system.purpose),
        system.it_approved,
        bool(system.deployment_date),
    ]
    return sum(checks) / len(checks) if checks else 0.0


# ── CRUD ────────────────────────────────────────────────────────

def register_ai_system(data: AISystemCreate) -> AISystem:
    """AIシステムを登録.

    Args:
        data: 登録情報

    Returns:
        AISystem: 登録されたAIシステム
    """
    risk_level = data.risk_level if data.risk_level is not None else classify_risk_level(data)

    system = AISystem(
        organization_id=data.organization_id,
        name=data.name,
        description=data.description,
        ai_type=data.ai_type,
        vendor=data.vendor,
        department=data.department,
        owner=data.owner,
        risk_level=risk_level,
        status=data.status,
        data_types=data.data_types,
        purpose=data.purpose,
        deployment_date=data.deployment_date,
        dependencies=data.dependencies,
        it_approved=data.it_approved,
    )
    system.governance_score = _calculate_governance_score(system)
    _ai_systems[system.id] = system
    return system


def get_ai_system(system_id: str) -> AISystem | None:
    """AIシステムを取得.

    Args:
        system_id: システムID

    Returns:
        AISystem | None: AIシステム or None
    """
    return _ai_systems.get(system_id)


def update_ai_system(system_id: str, update: AISystemUpdate) -> AISystem | None:
    """AIシステムを更新.

    Args:
        system_id: システムID
        update: 更新情報

    Returns:
        AISystem | None: 更新されたAIシステム or None
    """
    system = _ai_systems.get(system_id)
    if system is None:
        return None

    if update.name is not None:
        system.name = update.name
    if update.description is not None:
        system.description = update.description
    if update.ai_type is not None:
        system.ai_type = update.ai_type
    if update.vendor is not None:
        system.vendor = update.vendor
    if update.department is not None:
        system.department = update.department
    if update.owner is not None:
        system.owner = update.owner
    if update.risk_level is not None:
        system.risk_level = update.risk_level
    if update.status is not None:
        system.status = update.status
    if update.data_types is not None:
        system.data_types = update.data_types
    if update.purpose is not None:
        system.purpose = update.purpose
    if update.deployment_date is not None:
        system.deployment_date = update.deployment_date
    if update.dependencies is not None:
        system.dependencies = update.dependencies
    if update.it_approved is not None:
        system.it_approved = update.it_approved

    system.governance_score = _calculate_governance_score(system)
    system.updated_at = datetime.now(timezone.utc).isoformat()
    return system


def delete_ai_system(system_id: str) -> bool:
    """AIシステムを削除.

    Args:
        system_id: システムID

    Returns:
        bool: 削除成功
    """
    if system_id in _ai_systems:
        del _ai_systems[system_id]
        return True
    return False


def list_ai_systems(
    organization_id: str,
    status: AISystemStatus | None = None,
    risk_level: AISystemRiskLevel | None = None,
    department: str = "",
) -> list[AISystem]:
    """AIシステム一覧を取得.

    Args:
        organization_id: 組織ID
        status: フィルタ: ステータス
        risk_level: フィルタ: リスクレベル
        department: フィルタ: 部門

    Returns:
        list[AISystem]: AIシステムのリスト
    """
    result = [
        s for s in _ai_systems.values()
        if s.organization_id == organization_id
    ]
    if status is not None:
        result = [s for s in result if s.status == status]
    if risk_level is not None:
        result = [s for s in result if s.risk_level == risk_level]
    if department:
        result = [s for s in result if s.department == department]
    return result


# ── Shadow AI 検出 ──────────────────────────────────────────────

def detect_shadow_ai(organization_id: str) -> list[AISystem]:
    """Shadow AI（IT未承認のAIシステム）を検出.

    Args:
        organization_id: 組織ID

    Returns:
        list[AISystem]: IT未承認のAIシステムリスト
    """
    return [
        s for s in _ai_systems.values()
        if s.organization_id == organization_id and not s.it_approved
    ]


# ── 依存関係マッピング ──────────────────────────────────────────

def get_dependency_map(system_id: str) -> DependencyMap | None:
    """AIシステムの依存関係マップを取得.

    Args:
        system_id: システムID

    Returns:
        DependencyMap | None: 依存関係マップ or None
    """
    system = _ai_systems.get(system_id)
    if system is None:
        return None

    depends_on = []
    for dep_id in system.dependencies:
        dep = _ai_systems.get(dep_id)
        if dep:
            depends_on.append({"id": dep.id, "name": dep.name})

    depended_by = []
    for s in _ai_systems.values():
        if system_id in s.dependencies:
            depended_by.append({"id": s.id, "name": s.name})

    return DependencyMap(
        system_id=system.id,
        system_name=system.name,
        depends_on=depends_on,
        depended_by=depended_by,
    )


# ── ダッシュボード ──────────────────────────────────────────────

def get_registry_dashboard(organization_id: str) -> AIRegistryDashboard:
    """AIシステム台帳ダッシュボードを取得.

    Args:
        organization_id: 組織ID

    Returns:
        AIRegistryDashboard: ダッシュボード情報
    """
    systems = list_ai_systems(organization_id)

    by_risk: dict[str, int] = {}
    by_dept: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    total_gov_score = 0.0

    for s in systems:
        by_risk[s.risk_level.value] = by_risk.get(s.risk_level.value, 0) + 1
        if s.department:
            by_dept[s.department] = by_dept.get(s.department, 0) + 1
        by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
        by_type[s.ai_type.value] = by_type.get(s.ai_type.value, 0) + 1
        total_gov_score += s.governance_score

    shadow_count = len([s for s in systems if not s.it_approved])
    under_review = len([s for s in systems if s.status == AISystemStatus.UNDER_REVIEW])

    return AIRegistryDashboard(
        organization_id=organization_id,
        total_systems=len(systems),
        by_risk_level=by_risk,
        by_department=by_dept,
        by_status=by_status,
        by_type=by_type,
        under_review_count=under_review,
        shadow_ai_count=shadow_count,
        avg_governance_score=total_gov_score / len(systems) if systems else 0.0,
    )


# ── テスト用リセット ────────────────────────────────────────────

def reset_registry() -> None:
    """テスト用: ストレージをリセット."""
    _ai_systems.clear()
