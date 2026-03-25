# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Slack連携サービス.

Slack Webhook URLを介した自動通知:
- 定期レビューリマインダー（7日前、1日前）
- 承認リクエスト作成/承認/却下
- スコア閾値以下低下
- 新規Gap検出
- インシデント報告

通知テンプレートは日本語/英語対応。
テスト用にsend関数をモック可能にする。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

import httpx

from app.db.database import IntegrationConfigRow, get_db
from app.models import (
    IntegrationConfig,
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
)

logger = logging.getLogger(__name__)


# ── Webhook sender protocol (mockable) ──────────────────────────

class WebhookSender(Protocol):
    """Webhook送信のプロトコル（テスト用にモック可能）."""

    def __call__(self, url: str, payload: dict[str, Any]) -> bool: ...


def _default_sender(url: str, payload: dict[str, Any]) -> bool:
    """デフォルトのWebhook送信関数."""
    try:
        resp = httpx.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        logger.exception("Webhook送信失敗: %s", url)
        return False


# Module-level sender (テスト時に差し替え可能)
_sender: Callable[[str, dict[str, Any]], bool] = _default_sender


def set_webhook_sender(sender: Callable[[str, dict[str, Any]], bool]) -> None:
    """テスト用: Webhook送信関数を差し替える."""
    global _sender
    _sender = sender


def reset_webhook_sender() -> None:
    """テスト用: デフォルトの送信関数に戻す."""
    global _sender
    _sender = _default_sender


# ── Notification Templates ──────────────────────────────────────

TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "review_reminder": {
        "ja": {
            "title": "定期レビューのリマインダー",
            "body": "レビュー期限が近づいています。期限: {due_date}、サイクル: {cycle_type}",
        },
        "en": {
            "title": "Review Reminder",
            "body": "Review deadline approaching. Due: {due_date}, Cycle: {cycle_type}",
        },
    },
    "approval_created": {
        "ja": {
            "title": "承認リクエストが作成されました",
            "body": "「{title}」の承認が必要です。申請者: {requester}",
        },
        "en": {
            "title": "Approval Request Created",
            "body": "Approval needed for \"{title}\". Requester: {requester}",
        },
    },
    "approval_approved": {
        "ja": {
            "title": "承認されました",
            "body": "「{title}」が承認されました。承認者: {approver}",
        },
        "en": {
            "title": "Approved",
            "body": "\"{title}\" has been approved. Approver: {approver}",
        },
    },
    "approval_rejected": {
        "ja": {
            "title": "却下されました",
            "body": "「{title}」が却下されました。理由: {comment}",
        },
        "en": {
            "title": "Rejected",
            "body": "\"{title}\" has been rejected. Reason: {comment}",
        },
    },
    "score_drop": {
        "ja": {
            "title": "スコア低下アラート",
            "body": "成熟度スコアが閾値以下に低下しました。現在: {score}、閾値: {threshold}",
        },
        "en": {
            "title": "Score Drop Alert",
            "body": "Maturity score dropped below threshold. Current: {score}, Threshold: {threshold}",
        },
    },
    "new_gap": {
        "ja": {
            "title": "新しいGapが検出されました",
            "body": "要件 {req_id}: {req_title} でGapが検出されました。優先度: {priority}",
        },
        "en": {
            "title": "New Gap Detected",
            "body": "Gap detected for requirement {req_id}: {req_title}. Priority: {priority}",
        },
    },
    "incident_reported": {
        "ja": {
            "title": "AIインシデント報告",
            "body": "重大度: {severity} | 種別: {incident_type}\n{title}",
        },
        "en": {
            "title": "AI Incident Report",
            "body": "Severity: {severity} | Type: {incident_type}\n{title}",
        },
    },
    "monthly_report": {
        "ja": {
            "title": "月次レポートが生成されました",
            "body": "{year}年{month}月の月次レポートが利用可能です。",
        },
        "en": {
            "title": "Monthly Report Generated",
            "body": "Monthly report for {year}/{month} is now available.",
        },
    },
}


def _build_slack_payload(
    event_type: str,
    lang: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Slack Webhook用のペイロードを構築."""
    tpl = TEMPLATES.get(event_type, {}).get(lang, TEMPLATES.get(event_type, {}).get("ja", {}))
    if not tpl:
        return {"text": f"[JPGovAI] {event_type}: {json.dumps(params, ensure_ascii=False)}"}

    title = tpl["title"]
    body = tpl["body"].format_map({**{k: "" for k in _extract_placeholders(tpl["body"])}, **params})

    return {
        "text": f"[JPGovAI] {title}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n{body}",
                },
            },
        ],
    }


def _extract_placeholders(template: str) -> list[str]:
    """テンプレートからプレースホルダーを抽出."""
    import re
    return re.findall(r"\{(\w+)\}", template)


# ── Config CRUD ─────────────────────────────────────────────────

def create_integration_config(data: IntegrationConfigCreate) -> IntegrationConfig:
    """連携設定を作成."""
    config = IntegrationConfig(
        organization_id=data.organization_id,
        integration_type=data.integration_type,
        webhook_url=data.webhook_url,
        enabled=data.enabled,
        language=data.language,
    )
    db = get_db()
    with db.get_session() as session:
        row = IntegrationConfigRow(
            id=config.id,
            organization_id=config.organization_id,
            integration_type=config.integration_type,
            webhook_url=config.webhook_url,
            enabled=1 if config.enabled else 0,
            language=config.language,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
        session.add(row)
        session.commit()
    return config


def get_integration_config(
    organization_id: str,
    integration_type: str = "slack",
) -> IntegrationConfig | None:
    """連携設定を取得."""
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(IntegrationConfigRow)
            .filter_by(organization_id=organization_id, integration_type=integration_type)
            .first()
        )
        if row is None:
            return None
        return _config_row_to_model(row)


def update_integration_config(
    organization_id: str,
    integration_type: str,
    update: IntegrationConfigUpdate,
) -> IntegrationConfig | None:
    """連携設定を更新."""
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(IntegrationConfigRow)
            .filter_by(organization_id=organization_id, integration_type=integration_type)
            .first()
        )
        if row is None:
            return None

        if update.webhook_url is not None:
            row.webhook_url = update.webhook_url
        if update.enabled is not None:
            row.enabled = 1 if update.enabled else 0
        if update.notify_review_reminder is not None:
            row.notify_review_reminder = 1 if update.notify_review_reminder else 0
        if update.notify_approval is not None:
            row.notify_approval = 1 if update.notify_approval else 0
        if update.notify_incident is not None:
            row.notify_incident = 1 if update.notify_incident else 0
        if update.notify_score_drop is not None:
            row.notify_score_drop = 1 if update.notify_score_drop else 0
        if update.notify_new_gap is not None:
            row.notify_new_gap = 1 if update.notify_new_gap else 0
        if update.language is not None:
            row.language = update.language

        row.updated_at = datetime.now(timezone.utc).isoformat()
        session.commit()
        return _config_row_to_model(row)


def list_integration_configs(organization_id: str) -> list[IntegrationConfig]:
    """組織の連携設定一覧を取得."""
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(IntegrationConfigRow)
            .filter_by(organization_id=organization_id)
            .all()
        )
        return [_config_row_to_model(r) for r in rows]


# ── Notification dispatch ───────────────────────────────────────

def send_notification(
    organization_id: str,
    event_type: str,
    params: dict[str, Any],
) -> bool:
    """組織に設定されたWebhookに通知を送信.

    Args:
        organization_id: 組織ID
        event_type: イベントタイプ（テンプレートキー）
        params: テンプレートパラメータ

    Returns:
        bool: 送信成功したかどうか
    """
    config = get_integration_config(organization_id, "slack")
    if config is None or not config.enabled or not config.webhook_url:
        return False

    # イベントタイプに基づく通知設定チェック
    event_config_map = {
        "review_reminder": config.notify_review_reminder,
        "approval_created": config.notify_approval,
        "approval_approved": config.notify_approval,
        "approval_rejected": config.notify_approval,
        "score_drop": config.notify_score_drop,
        "new_gap": config.notify_new_gap,
        "incident_reported": config.notify_incident,
        "monthly_report": True,
    }
    if not event_config_map.get(event_type, True):
        return False

    payload = _build_slack_payload(event_type, config.language, params)
    return _sender(config.webhook_url, payload)


def notify_review_reminder(
    organization_id: str,
    due_date: str,
    cycle_type: str,
    days_until: int,
) -> bool:
    """レビューリマインダーを送信."""
    return send_notification(
        organization_id,
        "review_reminder",
        {"due_date": due_date, "cycle_type": cycle_type, "days_until": str(days_until)},
    )


def notify_approval_created(
    organization_id: str,
    title: str,
    requester: str,
) -> bool:
    """承認リクエスト作成通知."""
    return send_notification(
        organization_id,
        "approval_created",
        {"title": title, "requester": requester},
    )


def notify_approval_result(
    organization_id: str,
    title: str,
    approved: bool,
    approver: str = "",
    comment: str = "",
) -> bool:
    """承認/却下通知."""
    event = "approval_approved" if approved else "approval_rejected"
    return send_notification(
        organization_id,
        event,
        {"title": title, "approver": approver, "comment": comment},
    )


def notify_score_drop(
    organization_id: str,
    score: float,
    threshold: float,
) -> bool:
    """スコア低下通知."""
    return send_notification(
        organization_id,
        "score_drop",
        {"score": f"{score:.2f}", "threshold": f"{threshold:.2f}"},
    )


def notify_new_gap(
    organization_id: str,
    req_id: str,
    req_title: str,
    priority: str,
) -> bool:
    """新規Gap検出通知."""
    return send_notification(
        organization_id,
        "new_gap",
        {"req_id": req_id, "req_title": req_title, "priority": priority},
    )


def notify_incident(
    organization_id: str,
    title: str,
    severity: str,
    incident_type: str,
) -> bool:
    """インシデント通知."""
    return send_notification(
        organization_id,
        "incident_reported",
        {"title": title, "severity": severity, "incident_type": incident_type},
    )


def notify_monthly_report(
    organization_id: str,
    year: int,
    month: int,
) -> bool:
    """月次レポート生成通知."""
    return send_notification(
        organization_id,
        "monthly_report",
        {"year": str(year), "month": str(month)},
    )


# ── Internal helpers ────────────────────────────────────────────

def _config_row_to_model(row: IntegrationConfigRow) -> IntegrationConfig:
    """DBの行をモデルに変換."""
    return IntegrationConfig(
        id=row.id,
        organization_id=row.organization_id,
        integration_type=row.integration_type,
        webhook_url=row.webhook_url,
        enabled=bool(row.enabled),
        notify_review_reminder=bool(row.notify_review_reminder),
        notify_approval=bool(row.notify_approval),
        notify_incident=bool(row.notify_incident),
        notify_score_drop=bool(row.notify_score_drop),
        notify_new_gap=bool(row.notify_new_gap),
        language=row.language,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
