# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""エビデンス自動収集フレームワーク.

外部ソースからエビデンスを自動収集する:
- CollectorInterface: 各ソースの共通インターフェース
- GitHubCollector: リポジトリセキュリティ設定、branch protection、依存関係スキャン
- AWSCollector: IAMポリシー、CloudTrail、Config Rules
- JiraCollector: チケット完了状況
- ManualCollector: 手動アップロードのラッパー
- 自動収集スケジュール管理
- 収集結果の要件マッピング
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────

class CollectorType(str, Enum):
    """コレクター種別."""

    GITHUB = "github"
    AWS = "aws"
    JIRA = "jira"
    MANUAL = "manual"


class CollectionStatus(str, Enum):
    """収集ステータス."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


class ScheduleFrequency(str, Enum):
    """収集スケジュール頻度."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


# ── Models ───────────────────────────────────────────────────────

class CollectionResult(BaseModel):
    """収集結果."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    collector_type: CollectorType
    organization_id: str
    status: CollectionStatus = CollectionStatus.SUCCESS
    collected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    items_collected: int = 0
    items_mapped: int = 0
    evidence_items: list[CollectedEvidence] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectedEvidence(BaseModel):
    """収集されたエビデンスアイテム."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: CollectorType
    source_id: str = ""
    title: str = ""
    description: str = ""
    requirement_ids: list[str] = Field(default_factory=list)
    raw_data: dict[str, Any] = Field(default_factory=dict)
    collected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CollectorConfig(BaseModel):
    """コレクター設定."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    collector_type: CollectorType
    enabled: bool = True
    schedule: ScheduleFrequency = ScheduleFrequency.WEEKLY
    config: dict[str, Any] = Field(default_factory=dict)
    last_run: str = ""
    last_status: CollectionStatus = CollectionStatus.PENDING
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CollectionDashboard(BaseModel):
    """収集率ダッシュボード."""

    organization_id: str
    total_collectors: int = 0
    active_collectors: int = 0
    total_evidence_collected: int = 0
    total_mapped: int = 0
    coverage_rate: float = 0.0
    by_collector: dict[str, dict[str, Any]] = Field(default_factory=dict)
    last_collection: str = ""


# ── Forward reference fix ────────────────────────────────────────
# CollectionResult references CollectedEvidence, which is defined above
CollectionResult.model_rebuild()


# ── Collector Interface ──────────────────────────────────────────

class CollectorInterface(ABC):
    """コレクター共通インターフェース."""

    @abstractmethod
    def collector_type(self) -> CollectorType:
        """コレクター種別を返す."""
        ...

    @abstractmethod
    def collect(
        self,
        organization_id: str,
        config: dict[str, Any],
    ) -> CollectionResult:
        """エビデンスを収集する.

        Args:
            organization_id: 組織ID
            config: コレクター固有設定

        Returns:
            CollectionResult: 収集結果
        """
        ...

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """設定の妥当性を検証する.

        Args:
            config: コレクター設定

        Returns:
            list[str]: エラーメッセージのリスト（空=有効）
        """
        ...


# ── GitHub Collector ─────────────────────────────────────────────

# GitHub -> 要件IDマッピング
_GITHUB_REQUIREMENT_MAP: dict[str, list[str]] = {
    "branch_protection": ["REQ-009", "REQ-010"],  # セキュリティ管理
    "dependabot_alerts": ["REQ-009"],
    "code_scanning": ["REQ-009", "REQ-010"],
    "secret_scanning": ["REQ-009"],
    "security_policy": ["REQ-009", "REQ-010"],
}


class GitHubCollector(CollectorInterface):
    """GitHub リポジトリからエビデンスを収集.

    収集対象:
    - Branch protection設定
    - Dependabotアラート状況
    - Code scanning結果
    - Secret scanning設定
    - セキュリティポリシーの有無
    """

    def collector_type(self) -> CollectorType:
        return CollectorType.GITHUB

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        errors = []
        if not config.get("token"):
            errors.append("GitHub Personal Access Token is required")
        if not config.get("repos"):
            errors.append("At least one repository (owner/repo) is required")
        return errors

    def collect(
        self,
        organization_id: str,
        config: dict[str, Any],
    ) -> CollectionResult:
        """GitHubからエビデンスを収集（モック実装）.

        実際のAPI呼び出しはtokenが必要なため、
        設定に基づいたモックデータを返す。
        """
        repos = config.get("repos", [])
        evidence_items: list[CollectedEvidence] = []

        for repo in repos:
            # Branch protection check
            evidence_items.append(CollectedEvidence(
                source_type=CollectorType.GITHUB,
                source_id=f"{repo}/branch-protection",
                title=f"Branch Protection: {repo}",
                description="Branch protection設定の確認",
                requirement_ids=_GITHUB_REQUIREMENT_MAP.get("branch_protection", []),
                raw_data={"repo": repo, "check": "branch_protection", "status": "mock"},
            ))

            # Dependabot alerts
            evidence_items.append(CollectedEvidence(
                source_type=CollectorType.GITHUB,
                source_id=f"{repo}/dependabot",
                title=f"Dependabot Alerts: {repo}",
                description="依存関係の脆弱性スキャン結果",
                requirement_ids=_GITHUB_REQUIREMENT_MAP.get("dependabot_alerts", []),
                raw_data={"repo": repo, "check": "dependabot", "status": "mock"},
            ))

            # Security policy
            evidence_items.append(CollectedEvidence(
                source_type=CollectorType.GITHUB,
                source_id=f"{repo}/security-policy",
                title=f"Security Policy: {repo}",
                description="SECURITY.md の有無",
                requirement_ids=_GITHUB_REQUIREMENT_MAP.get("security_policy", []),
                raw_data={"repo": repo, "check": "security_policy", "status": "mock"},
            ))

        mapped_count = sum(1 for e in evidence_items if e.requirement_ids)

        return CollectionResult(
            collector_type=CollectorType.GITHUB,
            organization_id=organization_id,
            status=CollectionStatus.SUCCESS,
            items_collected=len(evidence_items),
            items_mapped=mapped_count,
            evidence_items=evidence_items,
            metadata={"repos": repos},
        )


# ── AWS Collector ────────────────────────────────────────────────

_AWS_REQUIREMENT_MAP: dict[str, list[str]] = {
    "iam_policies": ["REQ-009", "REQ-010"],
    "cloudtrail": ["REQ-010"],
    "config_rules": ["REQ-009"],
}


class AWSCollector(CollectorInterface):
    """AWS環境からエビデンスを収集（インターフェース定義）.

    収集対象:
    - IAMポリシー
    - CloudTrailログ
    - Config Rules準拠状況

    注: 実際のAWS API接続はクレデンシャルが必要なため、モック実装。
    """

    def collector_type(self) -> CollectorType:
        return CollectorType.AWS

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        errors = []
        if not config.get("aws_account_id"):
            errors.append("AWS Account ID is required")
        if not config.get("region"):
            errors.append("AWS Region is required")
        return errors

    def collect(
        self,
        organization_id: str,
        config: dict[str, Any],
    ) -> CollectionResult:
        """AWSからエビデンスを収集（モック実装）."""
        account_id = config.get("aws_account_id", "unknown")
        region = config.get("region", "ap-northeast-1")
        evidence_items: list[CollectedEvidence] = []

        # IAM policies check
        evidence_items.append(CollectedEvidence(
            source_type=CollectorType.AWS,
            source_id=f"aws/{account_id}/iam",
            title="IAM Policy Review",
            description="IAMポリシーの最小権限原則準拠状況",
            requirement_ids=_AWS_REQUIREMENT_MAP.get("iam_policies", []),
            raw_data={
                "account_id": account_id, "region": region,
                "check": "iam_policies", "status": "mock",
            },
        ))

        # CloudTrail check
        evidence_items.append(CollectedEvidence(
            source_type=CollectorType.AWS,
            source_id=f"aws/{account_id}/cloudtrail",
            title="CloudTrail Logging",
            description="CloudTrailログの有効化状況",
            requirement_ids=_AWS_REQUIREMENT_MAP.get("cloudtrail", []),
            raw_data={
                "account_id": account_id, "region": region,
                "check": "cloudtrail", "status": "mock",
            },
        ))

        # Config Rules check
        evidence_items.append(CollectedEvidence(
            source_type=CollectorType.AWS,
            source_id=f"aws/{account_id}/config-rules",
            title="AWS Config Rules Compliance",
            description="Config Rules準拠状況",
            requirement_ids=_AWS_REQUIREMENT_MAP.get("config_rules", []),
            raw_data={
                "account_id": account_id, "region": region,
                "check": "config_rules", "status": "mock",
            },
        ))

        mapped_count = sum(1 for e in evidence_items if e.requirement_ids)

        return CollectionResult(
            collector_type=CollectorType.AWS,
            organization_id=organization_id,
            status=CollectionStatus.SUCCESS,
            items_collected=len(evidence_items),
            items_mapped=mapped_count,
            evidence_items=evidence_items,
            metadata={"account_id": account_id, "region": region},
        )


# ── Jira Collector ───────────────────────────────────────────────

_JIRA_REQUIREMENT_MAP: dict[str, list[str]] = {
    "governance_tasks": ["REQ-001", "REQ-002"],
    "risk_tasks": ["REQ-003"],
    "security_tasks": ["REQ-009", "REQ-010"],
}


class JiraCollector(CollectorInterface):
    """Jiraからエビデンスを収集.

    収集対象:
    - ガバナンス関連チケットの完了状況
    - リスク対応チケットの完了状況
    - セキュリティ関連チケットの完了状況
    """

    def collector_type(self) -> CollectorType:
        return CollectorType.JIRA

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        errors = []
        if not config.get("jira_url"):
            errors.append("Jira URL is required")
        if not config.get("api_token"):
            errors.append("Jira API Token is required")
        if not config.get("project_key"):
            errors.append("Jira Project Key is required")
        return errors

    def collect(
        self,
        organization_id: str,
        config: dict[str, Any],
    ) -> CollectionResult:
        """Jiraからエビデンスを収集（モック実装）."""
        project_key = config.get("project_key", "UNKNOWN")
        evidence_items: list[CollectedEvidence] = []

        # Governance tasks
        evidence_items.append(CollectedEvidence(
            source_type=CollectorType.JIRA,
            source_id=f"jira/{project_key}/governance",
            title=f"Governance Tasks: {project_key}",
            description="ガバナンス関連タスクの完了状況",
            requirement_ids=_JIRA_REQUIREMENT_MAP.get("governance_tasks", []),
            raw_data={"project": project_key, "category": "governance", "status": "mock"},
        ))

        # Risk tasks
        evidence_items.append(CollectedEvidence(
            source_type=CollectorType.JIRA,
            source_id=f"jira/{project_key}/risk",
            title=f"Risk Tasks: {project_key}",
            description="リスク対応タスクの完了状況",
            requirement_ids=_JIRA_REQUIREMENT_MAP.get("risk_tasks", []),
            raw_data={"project": project_key, "category": "risk", "status": "mock"},
        ))

        mapped_count = sum(1 for e in evidence_items if e.requirement_ids)

        return CollectionResult(
            collector_type=CollectorType.JIRA,
            organization_id=organization_id,
            status=CollectionStatus.SUCCESS,
            items_collected=len(evidence_items),
            items_mapped=mapped_count,
            evidence_items=evidence_items,
            metadata={"project_key": project_key},
        )


# ── Manual Collector ─────────────────────────────────────────────

class ManualCollector(CollectorInterface):
    """手動アップロードのラッパー.

    既存のエビデンスアップロード機能をコレクターインターフェースで統一。
    """

    def collector_type(self) -> CollectorType:
        return CollectorType.MANUAL

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        return []  # 手動アップロードには設定不要

    def collect(
        self,
        organization_id: str,
        config: dict[str, Any],
    ) -> CollectionResult:
        """手動アップロード分のサマリーを生成."""
        return CollectionResult(
            collector_type=CollectorType.MANUAL,
            organization_id=organization_id,
            status=CollectionStatus.SUCCESS,
            items_collected=0,
            items_mapped=0,
            metadata={"note": "Manual uploads are tracked via evidence API"},
        )


# ── Collector Manager ────────────────────────────────────────────

_collector_configs: dict[str, CollectorConfig] = {}
_collection_results: dict[str, list[CollectionResult]] = {}

_collectors: dict[CollectorType, CollectorInterface] = {
    CollectorType.GITHUB: GitHubCollector(),
    CollectorType.AWS: AWSCollector(),
    CollectorType.JIRA: JiraCollector(),
    CollectorType.MANUAL: ManualCollector(),
}


def register_collector_config(
    organization_id: str,
    collector_type: CollectorType,
    config: dict[str, Any],
    schedule: ScheduleFrequency = ScheduleFrequency.WEEKLY,
) -> CollectorConfig:
    """コレクター設定を登録.

    Args:
        organization_id: 組織ID
        collector_type: コレクター種別
        config: コレクター固有設定
        schedule: 収集スケジュール

    Returns:
        CollectorConfig: 登録されたコレクター設定
    """
    collector = _collectors.get(collector_type)
    if collector:
        errors = collector.validate_config(config)
        if errors:
            return CollectorConfig(
                organization_id=organization_id,
                collector_type=collector_type,
                enabled=False,
                schedule=schedule,
                config=config,
                last_status=CollectionStatus.FAILURE,
            )

    cc = CollectorConfig(
        organization_id=organization_id,
        collector_type=collector_type,
        enabled=True,
        schedule=schedule,
        config=config,
    )
    _collector_configs[cc.id] = cc
    return cc


def get_collector_config(config_id: str) -> CollectorConfig | None:
    """コレクター設定を取得."""
    return _collector_configs.get(config_id)


def list_collector_configs(organization_id: str) -> list[CollectorConfig]:
    """コレクター設定一覧を取得."""
    return [
        c for c in _collector_configs.values()
        if c.organization_id == organization_id
    ]


def run_collection(
    config_id: str,
) -> CollectionResult | None:
    """指定されたコレクター設定で収集を実行.

    Args:
        config_id: コレクター設定ID

    Returns:
        CollectionResult | None: 収集結果
    """
    cc = _collector_configs.get(config_id)
    if cc is None:
        return None

    collector = _collectors.get(cc.collector_type)
    if collector is None:
        return None

    try:
        result = collector.collect(cc.organization_id, cc.config)
    except Exception as e:
        result = CollectionResult(
            collector_type=cc.collector_type,
            organization_id=cc.organization_id,
            status=CollectionStatus.FAILURE,
            errors=[str(e)],
        )

    cc.last_run = datetime.now(timezone.utc).isoformat()
    cc.last_status = result.status

    # 結果を保存
    org_key = cc.organization_id
    if org_key not in _collection_results:
        _collection_results[org_key] = []
    _collection_results[org_key].append(result)

    return result


def run_all_collections(organization_id: str) -> list[CollectionResult]:
    """組織の全有効コレクターで収集を実行.

    Args:
        organization_id: 組織ID

    Returns:
        list[CollectionResult]: 収集結果リスト
    """
    configs = list_collector_configs(organization_id)
    results = []
    for cc in configs:
        if cc.enabled:
            result = run_collection(cc.id)
            if result:
                results.append(result)
    return results


def get_collection_dashboard(organization_id: str) -> CollectionDashboard:
    """収集率ダッシュボードを取得.

    Args:
        organization_id: 組織ID

    Returns:
        CollectionDashboard: ダッシュボード情報
    """
    configs = list_collector_configs(organization_id)
    results = _collection_results.get(organization_id, [])

    active = sum(1 for c in configs if c.enabled)
    total_collected = sum(r.items_collected for r in results)
    total_mapped = sum(r.items_mapped for r in results)

    by_collector: dict[str, dict[str, Any]] = {}
    for c in configs:
        collector_results = [r for r in results if r.collector_type == c.collector_type]
        last_result = collector_results[-1] if collector_results else None
        by_collector[c.collector_type.value] = {
            "enabled": c.enabled,
            "schedule": c.schedule.value,
            "last_run": c.last_run,
            "last_status": c.last_status.value,
            "items_collected": sum(r.items_collected for r in collector_results),
            "items_mapped": sum(r.items_mapped for r in collector_results),
        }

    last_run_dates = [c.last_run for c in configs if c.last_run]
    last_collection = max(last_run_dates) if last_run_dates else ""

    # Coverage rate = unique mapped requirements / total requirements
    all_mapped_reqs: set[str] = set()
    for r in results:
        for item in r.evidence_items:
            all_mapped_reqs.update(item.requirement_ids)

    # Approximate total requirements (from METI guidelines)
    total_reqs = 20  # approximate
    coverage = len(all_mapped_reqs) / total_reqs if total_reqs > 0 else 0.0

    return CollectionDashboard(
        organization_id=organization_id,
        total_collectors=len(configs),
        active_collectors=active,
        total_evidence_collected=total_collected,
        total_mapped=total_mapped,
        coverage_rate=min(coverage, 1.0),
        by_collector=by_collector,
        last_collection=last_collection,
    )


# ── テスト用リセット ────────────────────────────────────────────

def reset_collectors() -> None:
    """テスト用: ストレージをリセット."""
    _collector_configs.clear()
    _collection_results.clear()
