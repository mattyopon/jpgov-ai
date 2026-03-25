# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Public API for external integrations.

外部連携用のREST API。API Key認証、Rate Limiting、
Webhook outgoing等を提供する。

エンドポイント:
- GET  /api/v1/assessments      — 診断結果取得
- GET  /api/v1/gaps             — Gapリスト取得
- GET  /api/v1/incidents        — インシデント一覧
- GET  /api/v1/compliance-score — 準拠スコア取得
- POST /api/v1/evidence         — エビデンスの外部登録
- GET  /api/v1/benchmark        — 業界ベンチマーク
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any



# ── API Key Management ───────────────────────────────────

class APIKeyManager:
    """API Key管理.

    シンプルなインメモリ実装。本番環境ではDBベースに移行する。
    """

    def __init__(self) -> None:
        self._keys: dict[str, dict[str, Any]] = {}

    def create_key(
        self,
        organization_id: str,
        name: str = "",
        scopes: list[str] | None = None,
    ) -> dict[str, str]:
        """API Keyを発行.

        Args:
            organization_id: 組織ID
            name: キーの名前（識別用）
            scopes: 許可スコープ (read, write, admin)

        Returns:
            {"api_key": str, "key_id": str}
        """
        key_id = str(uuid.uuid4())
        raw_key = f"jpgov_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        self._keys[key_hash] = {
            "key_id": key_id,
            "organization_id": organization_id,
            "name": name or f"key-{key_id[:8]}",
            "scopes": scopes or ["read"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }

        return {"api_key": raw_key, "key_id": key_id}

    def validate_key(self, api_key: str) -> dict[str, Any] | None:
        """API Keyを検証.

        Args:
            api_key: 検証するAPI Key

        Returns:
            キー情報の辞書。無効な場合はNone。
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        info = self._keys.get(key_hash)
        if info and info.get("active"):
            return info
        return None

    def revoke_key(self, key_id: str) -> bool:
        """API Keyを無効化.

        Args:
            key_id: 無効化するキーID

        Returns:
            成功したかどうか
        """
        for key_hash, info in self._keys.items():
            if info["key_id"] == key_id:
                info["active"] = False
                return True
        return False

    def list_keys(self, organization_id: str) -> list[dict[str, Any]]:
        """組織のAPI Key一覧.

        Args:
            organization_id: 組織ID

        Returns:
            キー情報のリスト（api_key自体は含まない）
        """
        return [
            {
                "key_id": info["key_id"],
                "name": info["name"],
                "scopes": info["scopes"],
                "active": info["active"],
                "created_at": info["created_at"],
            }
            for info in self._keys.values()
            if info["organization_id"] == organization_id
        ]


# ── Rate Limiter ─────────────────────────────────────────

class RateLimiter:
    """シンプルなToken Bucket Rate Limiter."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        """リクエストが許可されるか確認.

        Args:
            key: レート制限のキー（通常はAPI Key ID）

        Returns:
            許可される場合True
        """
        now = time.time()
        bucket = self._buckets[key]

        # 古いエントリを削除
        self._buckets[key] = [
            t for t in bucket if now - t < self.window_seconds
        ]

        if len(self._buckets[key]) >= self.max_requests:
            return False

        self._buckets[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """残りリクエスト数を取得.

        Args:
            key: レート制限のキー

        Returns:
            残りリクエスト数
        """
        now = time.time()
        bucket = self._buckets.get(key, [])
        active = [t for t in bucket if now - t < self.window_seconds]
        return max(0, self.max_requests - len(active))


# ── Webhook Manager ──────────────────────────────────────

class WebhookConfig:
    """Webhook設定."""

    def __init__(
        self,
        organization_id: str,
        url: str,
        events: list[str] | None = None,
        secret: str = "",
        active: bool = True,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.url = url
        self.events = events or ["*"]
        self.secret = secret or uuid.uuid4().hex
        self.active = active
        self.created_at = datetime.now(timezone.utc).isoformat()


class WebhookManager:
    """Webhook outgoing管理."""

    def __init__(self) -> None:
        self._configs: dict[str, WebhookConfig] = {}
        self._delivery_log: list[dict[str, Any]] = []

    def register(
        self,
        organization_id: str,
        url: str,
        events: list[str] | None = None,
    ) -> WebhookConfig:
        """Webhookを登録.

        Args:
            organization_id: 組織ID
            url: WebhookのURL
            events: 購読イベント一覧

        Returns:
            WebhookConfig: 登録された設定
        """
        config = WebhookConfig(
            organization_id=organization_id,
            url=url,
            events=events,
        )
        self._configs[config.id] = config
        return config

    def unregister(self, webhook_id: str) -> bool:
        """Webhook登録解除.

        Args:
            webhook_id: Webhook ID

        Returns:
            成功したかどうか
        """
        if webhook_id in self._configs:
            del self._configs[webhook_id]
            return True
        return False

    def list_webhooks(self, organization_id: str) -> list[dict[str, Any]]:
        """組織のWebhook一覧.

        Args:
            organization_id: 組織ID

        Returns:
            Webhook設定のリスト
        """
        return [
            {
                "id": c.id,
                "url": c.url,
                "events": c.events,
                "active": c.active,
                "created_at": c.created_at,
            }
            for c in self._configs.values()
            if c.organization_id == organization_id
        ]

    def prepare_delivery(
        self,
        organization_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Webhook配信を準備.

        実際のHTTP送信は呼び出し側が行う（テスタビリティのため）。

        Args:
            organization_id: 組織ID
            event_type: イベント種別
            payload: ペイロード

        Returns:
            配信すべきWebhookのリスト
        """
        deliveries: list[dict[str, Any]] = []
        for config in self._configs.values():
            if config.organization_id != organization_id:
                continue
            if not config.active:
                continue
            if "*" not in config.events and event_type not in config.events:
                continue

            body = {
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "organization_id": organization_id,
                "data": payload,
            }

            body_str = json.dumps(body, ensure_ascii=False, sort_keys=True)
            signature = hmac.new(
                config.secret.encode(),
                body_str.encode(),
                hashlib.sha256,
            ).hexdigest()

            delivery = {
                "webhook_id": config.id,
                "url": config.url,
                "body": body,
                "headers": {
                    "Content-Type": "application/json",
                    "X-JPGovAI-Signature": f"sha256={signature}",
                    "X-JPGovAI-Event": event_type,
                },
            }
            deliveries.append(delivery)

            self._delivery_log.append({
                "webhook_id": config.id,
                "event_type": event_type,
                "timestamp": body["timestamp"],
                "status": "prepared",
            })

        return deliveries

    def get_delivery_log(
        self,
        organization_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """配信ログを取得.

        Args:
            organization_id: 組織ID
            limit: 最大件数

        Returns:
            配信ログのリスト
        """
        org_webhooks = {
            c.id
            for c in self._configs.values()
            if c.organization_id == organization_id
        }
        return [
            entry
            for entry in reversed(self._delivery_log)
            if entry["webhook_id"] in org_webhooks
        ][:limit]


# ── Public API Response Builders ─────────────────────────

def build_assessment_response(
    assessment_data: dict[str, Any],
) -> dict[str, Any]:
    """診断結果のPublic APIレスポンスを構築.

    Args:
        assessment_data: 診断データ

    Returns:
        整形されたレスポンス
    """
    return {
        "id": assessment_data.get("id", ""),
        "organization_id": assessment_data.get("organization_id", ""),
        "overall_score": assessment_data.get("overall_score", 0.0),
        "maturity_level": assessment_data.get("maturity_level", 1),
        "category_scores": assessment_data.get("category_scores", []),
        "timestamp": assessment_data.get("timestamp", ""),
    }


def build_compliance_score_response(
    organization_id: str,
    meti_score: float = 0.0,
    iso_score: float = 0.0,
    act_score: float = 0.0,
    overall_rate: float = 0.0,
) -> dict[str, Any]:
    """準拠スコアのPublic APIレスポンスを構築.

    Args:
        organization_id: 組織ID
        meti_score: METIスコア
        iso_score: ISO 42001スコア
        act_score: AI推進法スコア
        overall_rate: 全体準拠率

    Returns:
        整形されたレスポンス
    """
    return {
        "organization_id": organization_id,
        "scores": {
            "meti_guideline": meti_score,
            "iso42001": iso_score,
            "ai_promotion_act": act_score,
        },
        "overall_compliance_rate": overall_rate,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Singleton Instances ──────────────────────────────────

_api_key_manager: APIKeyManager | None = None
_rate_limiter: RateLimiter | None = None
_webhook_manager: WebhookManager | None = None


def get_api_key_manager() -> APIKeyManager:
    """APIKeyManagerのシングルトンを取得."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def get_rate_limiter() -> RateLimiter:
    """RateLimiterのシングルトンを取得."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_webhook_manager() -> WebhookManager:
    """WebhookManagerのシングルトンを取得."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


def reset_public_api() -> None:
    """シングルトンをリセット（テスト用）."""
    global _api_key_manager, _rate_limiter, _webhook_manager
    _api_key_manager = None
    _rate_limiter = None
    _webhook_manager = None
