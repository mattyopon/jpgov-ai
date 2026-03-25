# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Integration Hub - 外部ツール連携の統合管理.

外部ツール連携を統一インターフェースで管理:
- IntegrationProvider: 連携先の定義
- 対応プロバイダー一覧
- 接続設定管理（OAuth/API Key/Webhook）
- イベントルーティング
- 連携ステータスダッシュボード
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────

class ProviderCategory(str, Enum):
    """プロバイダーカテゴリ."""

    COMMUNICATION = "communication"
    PROJECT = "project"
    DOCUMENT = "document"
    CLOUD = "cloud"
    CODE = "code"
    IDENTITY = "identity"


class AuthType(str, Enum):
    """認証種別."""

    OAUTH = "oauth"
    API_KEY = "api_key"
    WEBHOOK = "webhook"
    BASIC = "basic"
    NONE = "none"


class IntegrationStatus(str, Enum):
    """連携ステータス."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class EventType(str, Enum):
    """JPGovAI内部イベント種別."""

    ASSESSMENT_COMPLETED = "assessment.completed"
    GAP_DETECTED = "gap.detected"
    INCIDENT_CREATED = "incident.created"
    INCIDENT_RESOLVED = "incident.resolved"
    REVIEW_REMINDER = "review.reminder"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_COMPLETED = "approval.completed"
    SCORE_CHANGED = "score.changed"
    EVIDENCE_UPLOADED = "evidence.uploaded"
    REPORT_GENERATED = "report.generated"


# ── Models ───────────────────────────────────────────────────────

class ProviderDefinition(BaseModel):
    """プロバイダー定義（静的）."""

    id: str
    name: str
    category: ProviderCategory
    auth_types: list[AuthType] = Field(default_factory=list)
    description: str = ""
    config_fields: list[dict[str, str]] = Field(default_factory=list)
    supported_events: list[EventType] = Field(default_factory=list)
    icon: str = ""


class IntegrationConnection(BaseModel):
    """連携接続設定."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    provider_id: str
    auth_type: AuthType = AuthType.API_KEY
    credentials: dict[str, str] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    subscribed_events: list[str] = Field(default_factory=list)
    last_sync: str = ""
    error_message: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class IntegrationConnectionCreate(BaseModel):
    """連携接続作成リクエスト."""

    organization_id: str
    provider_id: str
    auth_type: AuthType = AuthType.API_KEY
    credentials: dict[str, str] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    subscribed_events: list[str] = Field(default_factory=list)


class IntegrationConnectionUpdate(BaseModel):
    """連携接続更新リクエスト."""

    credentials: dict[str, str] | None = None
    config: dict[str, Any] | None = None
    subscribed_events: list[str] | None = None
    status: IntegrationStatus | None = None


class EventRouting(BaseModel):
    """イベントルーティング結果."""

    event_type: str
    routed_to: list[str] = Field(default_factory=list)
    results: dict[str, str] = Field(default_factory=dict)


class IntegrationHubDashboard(BaseModel):
    """Integration Hubダッシュボード."""

    organization_id: str
    total_providers: int = 0
    connected_count: int = 0
    error_count: int = 0
    by_category: dict[str, dict[str, Any]] = Field(default_factory=dict)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)
    connections: list[IntegrationConnection] = Field(default_factory=list)


# ── Provider Registry (Static) ──────────────────────────────────

PROVIDERS: dict[str, ProviderDefinition] = {
    # Communication
    "slack": ProviderDefinition(
        id="slack",
        name="Slack",
        category=ProviderCategory.COMMUNICATION,
        auth_types=[AuthType.WEBHOOK, AuthType.OAUTH],
        description="Slack Workspace連携。通知・アラート配信。",
        config_fields=[
            {"name": "webhook_url", "label": "Webhook URL", "type": "url"},
            {"name": "channel", "label": "Channel", "type": "text"},
        ],
        supported_events=[
            EventType.INCIDENT_CREATED, EventType.REVIEW_REMINDER,
            EventType.APPROVAL_REQUESTED, EventType.SCORE_CHANGED,
            EventType.GAP_DETECTED, EventType.REPORT_GENERATED,
        ],
        icon="slack",
    ),
    "teams": ProviderDefinition(
        id="teams",
        name="Microsoft Teams",
        category=ProviderCategory.COMMUNICATION,
        auth_types=[AuthType.WEBHOOK],
        description="Microsoft Teams連携。通知・アラート配信。",
        config_fields=[
            {"name": "webhook_url", "label": "Incoming Webhook URL", "type": "url"},
        ],
        supported_events=[
            EventType.INCIDENT_CREATED, EventType.REVIEW_REMINDER,
            EventType.APPROVAL_REQUESTED, EventType.SCORE_CHANGED,
        ],
        icon="teams",
    ),
    "email": ProviderDefinition(
        id="email",
        name="Email (SMTP)",
        category=ProviderCategory.COMMUNICATION,
        auth_types=[AuthType.BASIC],
        description="メール通知。SMTP設定による配信。",
        config_fields=[
            {"name": "smtp_host", "label": "SMTP Host", "type": "text"},
            {"name": "smtp_port", "label": "SMTP Port", "type": "number"},
            {"name": "from_address", "label": "送信元アドレス", "type": "email"},
        ],
        supported_events=[
            EventType.INCIDENT_CREATED, EventType.REVIEW_REMINDER,
            EventType.APPROVAL_REQUESTED, EventType.REPORT_GENERATED,
        ],
        icon="email",
    ),
    # Project
    "jira": ProviderDefinition(
        id="jira",
        name="Jira",
        category=ProviderCategory.PROJECT,
        auth_types=[AuthType.API_KEY, AuthType.OAUTH],
        description="Jiraプロジェクト連携。タスク同期・エビデンス収集。",
        config_fields=[
            {"name": "jira_url", "label": "Jira URL", "type": "url"},
            {"name": "project_key", "label": "Project Key", "type": "text"},
        ],
        supported_events=[
            EventType.GAP_DETECTED, EventType.INCIDENT_CREATED,
        ],
        icon="jira",
    ),
    "asana": ProviderDefinition(
        id="asana",
        name="Asana",
        category=ProviderCategory.PROJECT,
        auth_types=[AuthType.API_KEY, AuthType.OAUTH],
        description="Asanaプロジェクト連携。タスク同期。",
        config_fields=[
            {"name": "workspace_id", "label": "Workspace ID", "type": "text"},
            {"name": "project_id", "label": "Project ID", "type": "text"},
        ],
        supported_events=[
            EventType.GAP_DETECTED, EventType.INCIDENT_CREATED,
        ],
        icon="asana",
    ),
    "trello": ProviderDefinition(
        id="trello",
        name="Trello",
        category=ProviderCategory.PROJECT,
        auth_types=[AuthType.API_KEY],
        description="Trelloボード連携。カード同期。",
        config_fields=[
            {"name": "board_id", "label": "Board ID", "type": "text"},
        ],
        supported_events=[EventType.GAP_DETECTED],
        icon="trello",
    ),
    # Document
    "confluence": ProviderDefinition(
        id="confluence",
        name="Confluence",
        category=ProviderCategory.DOCUMENT,
        auth_types=[AuthType.API_KEY, AuthType.OAUTH],
        description="Confluence連携。ポリシー文書の同期。",
        config_fields=[
            {"name": "confluence_url", "label": "Confluence URL", "type": "url"},
            {"name": "space_key", "label": "Space Key", "type": "text"},
        ],
        supported_events=[EventType.REPORT_GENERATED, EventType.EVIDENCE_UPLOADED],
        icon="confluence",
    ),
    "sharepoint": ProviderDefinition(
        id="sharepoint",
        name="SharePoint",
        category=ProviderCategory.DOCUMENT,
        auth_types=[AuthType.OAUTH],
        description="SharePoint連携。文書管理・エビデンス保管。",
        config_fields=[
            {"name": "site_url", "label": "Site URL", "type": "url"},
            {"name": "library_name", "label": "Document Library", "type": "text"},
        ],
        supported_events=[EventType.REPORT_GENERATED, EventType.EVIDENCE_UPLOADED],
        icon="sharepoint",
    ),
    "google_drive": ProviderDefinition(
        id="google_drive",
        name="Google Drive",
        category=ProviderCategory.DOCUMENT,
        auth_types=[AuthType.OAUTH],
        description="Google Drive連携。文書管理。",
        config_fields=[
            {"name": "folder_id", "label": "Folder ID", "type": "text"},
        ],
        supported_events=[EventType.REPORT_GENERATED, EventType.EVIDENCE_UPLOADED],
        icon="google_drive",
    ),
    # Cloud
    "aws": ProviderDefinition(
        id="aws",
        name="Amazon Web Services",
        category=ProviderCategory.CLOUD,
        auth_types=[AuthType.API_KEY],
        description="AWS連携。セキュリティ設定・ログ収集。",
        config_fields=[
            {"name": "account_id", "label": "Account ID", "type": "text"},
            {"name": "region", "label": "Region", "type": "text"},
        ],
        supported_events=[EventType.EVIDENCE_UPLOADED],
        icon="aws",
    ),
    "azure": ProviderDefinition(
        id="azure",
        name="Microsoft Azure",
        category=ProviderCategory.CLOUD,
        auth_types=[AuthType.OAUTH],
        description="Azure連携。セキュリティ設定・ログ収集。",
        config_fields=[
            {"name": "tenant_id", "label": "Tenant ID", "type": "text"},
            {"name": "subscription_id", "label": "Subscription ID", "type": "text"},
        ],
        supported_events=[EventType.EVIDENCE_UPLOADED],
        icon="azure",
    ),
    "gcp": ProviderDefinition(
        id="gcp",
        name="Google Cloud Platform",
        category=ProviderCategory.CLOUD,
        auth_types=[AuthType.OAUTH],
        description="GCP連携。セキュリティ設定・ログ収集。",
        config_fields=[
            {"name": "project_id", "label": "Project ID", "type": "text"},
        ],
        supported_events=[EventType.EVIDENCE_UPLOADED],
        icon="gcp",
    ),
    # Code
    "github": ProviderDefinition(
        id="github",
        name="GitHub",
        category=ProviderCategory.CODE,
        auth_types=[AuthType.API_KEY, AuthType.OAUTH],
        description="GitHub連携。リポジトリセキュリティ・エビデンス収集。",
        config_fields=[
            {"name": "org_name", "label": "Organization Name", "type": "text"},
        ],
        supported_events=[EventType.EVIDENCE_UPLOADED],
        icon="github",
    ),
    "gitlab": ProviderDefinition(
        id="gitlab",
        name="GitLab",
        category=ProviderCategory.CODE,
        auth_types=[AuthType.API_KEY, AuthType.OAUTH],
        description="GitLab連携。リポジトリセキュリティ・エビデンス収集。",
        config_fields=[
            {"name": "gitlab_url", "label": "GitLab URL", "type": "url"},
            {"name": "group_id", "label": "Group ID", "type": "text"},
        ],
        supported_events=[EventType.EVIDENCE_UPLOADED],
        icon="gitlab",
    ),
    # Identity
    "okta": ProviderDefinition(
        id="okta",
        name="Okta",
        category=ProviderCategory.IDENTITY,
        auth_types=[AuthType.API_KEY, AuthType.OAUTH],
        description="Okta連携。SSO・ユーザー管理。",
        config_fields=[
            {"name": "okta_domain", "label": "Okta Domain", "type": "url"},
        ],
        supported_events=[],
        icon="okta",
    ),
    "azure_ad": ProviderDefinition(
        id="azure_ad",
        name="Azure Active Directory",
        category=ProviderCategory.IDENTITY,
        auth_types=[AuthType.OAUTH],
        description="Azure AD連携。SSO・ディレクトリ統合。",
        config_fields=[
            {"name": "tenant_id", "label": "Tenant ID", "type": "text"},
        ],
        supported_events=[],
        icon="azure_ad",
    ),
}


# ── In-memory storage ────────────────────────────────────────────

_connections: dict[str, IntegrationConnection] = {}
_event_log: list[dict[str, Any]] = []


# ── Provider functions ───────────────────────────────────────────

def list_providers(
    category: ProviderCategory | None = None,
) -> list[ProviderDefinition]:
    """利用可能なプロバイダー一覧を取得.

    Args:
        category: フィルタ: カテゴリ

    Returns:
        list[ProviderDefinition]: プロバイダーリスト
    """
    providers = list(PROVIDERS.values())
    if category is not None:
        providers = [p for p in providers if p.category == category]
    return providers


def get_provider(provider_id: str) -> ProviderDefinition | None:
    """プロバイダー定義を取得."""
    return PROVIDERS.get(provider_id)


# ── Connection CRUD ──────────────────────────────────────────────

def create_connection(data: IntegrationConnectionCreate) -> IntegrationConnection:
    """連携接続を作成.

    Args:
        data: 接続情報

    Returns:
        IntegrationConnection: 作成された接続
    """
    provider = PROVIDERS.get(data.provider_id)
    if provider is None:
        conn = IntegrationConnection(
            organization_id=data.organization_id,
            provider_id=data.provider_id,
            auth_type=data.auth_type,
            credentials=data.credentials,
            config=data.config,
            status=IntegrationStatus.ERROR,
            error_message="Unknown provider",
            subscribed_events=data.subscribed_events,
        )
        _connections[conn.id] = conn
        return conn

    # Validate auth type
    if data.auth_type not in provider.auth_types:
        status = IntegrationStatus.ERROR
        error_msg = f"Auth type {data.auth_type.value} not supported for {provider.name}"
    else:
        status = IntegrationStatus.CONNECTED
        error_msg = ""

    conn = IntegrationConnection(
        organization_id=data.organization_id,
        provider_id=data.provider_id,
        auth_type=data.auth_type,
        credentials=data.credentials,
        config=data.config,
        status=status,
        error_message=error_msg,
        subscribed_events=data.subscribed_events,
    )
    _connections[conn.id] = conn
    return conn


def get_connection(connection_id: str) -> IntegrationConnection | None:
    """連携接続を取得."""
    return _connections.get(connection_id)


def update_connection(
    connection_id: str,
    update: IntegrationConnectionUpdate,
) -> IntegrationConnection | None:
    """連携接続を更新."""
    conn = _connections.get(connection_id)
    if conn is None:
        return None

    if update.credentials is not None:
        conn.credentials = update.credentials
    if update.config is not None:
        conn.config = update.config
    if update.subscribed_events is not None:
        conn.subscribed_events = update.subscribed_events
    if update.status is not None:
        conn.status = update.status

    conn.updated_at = datetime.now(timezone.utc).isoformat()
    return conn


def delete_connection(connection_id: str) -> bool:
    """連携接続を削除."""
    if connection_id in _connections:
        del _connections[connection_id]
        return True
    return False


def list_connections(
    organization_id: str,
    category: ProviderCategory | None = None,
) -> list[IntegrationConnection]:
    """組織の連携接続一覧を取得."""
    result = [
        c for c in _connections.values()
        if c.organization_id == organization_id
    ]
    if category is not None:
        provider_ids = {
            p.id for p in PROVIDERS.values() if p.category == category
        }
        result = [c for c in result if c.provider_id in provider_ids]
    return result


# ── Event Routing ────────────────────────────────────────────────

def route_event(
    organization_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> EventRouting:
    """JPGovAI内イベントを適切な連携先に配信.

    Args:
        organization_id: 組織ID
        event_type: イベント種別
        payload: イベントペイロード

    Returns:
        EventRouting: ルーティング結果
    """
    connections = list_connections(organization_id)
    routed_to: list[str] = []
    results: dict[str, str] = {}

    for conn in connections:
        if conn.status != IntegrationStatus.CONNECTED:
            continue
        if event_type in conn.subscribed_events or "*" in conn.subscribed_events:
            provider = PROVIDERS.get(conn.provider_id)
            provider_name = provider.name if provider else conn.provider_id
            routed_to.append(provider_name)
            # In production, this would actually send the event
            results[provider_name] = "delivered"

    # Log the event
    _event_log.append({
        "organization_id": organization_id,
        "event_type": event_type,
        "payload": payload,
        "routed_to": routed_to,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return EventRouting(
        event_type=event_type,
        routed_to=routed_to,
        results=results,
    )


# ── Dashboard ────────────────────────────────────────────────────

def get_hub_dashboard(organization_id: str) -> IntegrationHubDashboard:
    """Integration Hubダッシュボードを取得.

    Args:
        organization_id: 組織ID

    Returns:
        IntegrationHubDashboard: ダッシュボード情報
    """
    connections = list_connections(organization_id)

    connected = sum(1 for c in connections if c.status == IntegrationStatus.CONNECTED)
    errors = sum(1 for c in connections if c.status == IntegrationStatus.ERROR)

    by_category: dict[str, dict[str, Any]] = {}
    for cat in ProviderCategory:
        cat_providers = [p.id for p in PROVIDERS.values() if p.category == cat]
        cat_connections = [c for c in connections if c.provider_id in cat_providers]
        by_category[cat.value] = {
            "available": len(cat_providers),
            "connected": sum(1 for c in cat_connections if c.status == IntegrationStatus.CONNECTED),
            "providers": cat_providers,
        }

    recent = [
        e for e in _event_log
        if e.get("organization_id") == organization_id
    ][-10:]  # last 10 events

    return IntegrationHubDashboard(
        organization_id=organization_id,
        total_providers=len(PROVIDERS),
        connected_count=connected,
        error_count=errors,
        by_category=by_category,
        recent_events=recent,
        connections=connections,
    )


# ── テスト用リセット ────────────────────────────────────────────

def reset_hub() -> None:
    """テスト用: ストレージをリセット."""
    _connections.clear()
    _event_log.clear()
