# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for public API service."""

from __future__ import annotations


import pytest

from app.api.public_api import (
    APIKeyManager,
    RateLimiter,
    WebhookManager,
    build_assessment_response,
    build_compliance_score_response,
    get_api_key_manager,
    get_rate_limiter,
    get_webhook_manager,
    reset_public_api,
)


@pytest.fixture(autouse=True)
def _reset():
    """Reset singletons for each test."""
    reset_public_api()
    yield
    reset_public_api()


class TestAPIKeyManager:
    """API Key管理のテスト."""

    def test_create_key(self):
        """キーが作成できること."""
        mgr = APIKeyManager()
        result = mgr.create_key("org-1", "test-key")
        assert "api_key" in result
        assert "key_id" in result
        assert result["api_key"].startswith("jpgov_")

    def test_validate_key(self):
        """有効なキーが検証できること."""
        mgr = APIKeyManager()
        result = mgr.create_key("org-1")
        info = mgr.validate_key(result["api_key"])
        assert info is not None
        assert info["organization_id"] == "org-1"

    def test_validate_invalid_key(self):
        """無効なキーでNone."""
        mgr = APIKeyManager()
        assert mgr.validate_key("invalid-key") is None

    def test_revoke_key(self):
        """キーを無効化できること."""
        mgr = APIKeyManager()
        result = mgr.create_key("org-1")
        assert mgr.revoke_key(result["key_id"]) is True
        assert mgr.validate_key(result["api_key"]) is None

    def test_revoke_nonexistent_key(self):
        """存在しないキーの無効化はFalse."""
        mgr = APIKeyManager()
        assert mgr.revoke_key("nonexistent") is False

    def test_list_keys(self):
        """キー一覧が取得できること."""
        mgr = APIKeyManager()
        mgr.create_key("org-1", "key-1")
        mgr.create_key("org-1", "key-2")
        mgr.create_key("org-2", "key-3")

        keys = mgr.list_keys("org-1")
        assert len(keys) == 2

    def test_scopes(self):
        """スコープが設定できること."""
        mgr = APIKeyManager()
        result = mgr.create_key("org-1", scopes=["read", "write"])
        info = mgr.validate_key(result["api_key"])
        assert info is not None
        assert info["scopes"] == ["read", "write"]


class TestRateLimiter:
    """Rate Limiterのテスト."""

    def test_allows_within_limit(self):
        """制限内のリクエストが許可されること."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.check("key-1") is True

    def test_blocks_over_limit(self):
        """制限超過のリクエストが拒否されること."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("key-1")
        assert limiter.check("key-1") is False

    def test_different_keys_independent(self):
        """異なるキーは独立していること."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.check("key-1")
        limiter.check("key-1")
        assert limiter.check("key-1") is False
        assert limiter.check("key-2") is True

    def test_get_remaining(self):
        """残りリクエスト数が取得できること."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.get_remaining("key-1") == 5
        limiter.check("key-1")
        assert limiter.get_remaining("key-1") == 4


class TestWebhookManager:
    """Webhook管理のテスト."""

    def test_register_webhook(self):
        """Webhookを登録できること."""
        mgr = WebhookManager()
        config = mgr.register("org-1", "https://example.com/webhook")
        assert config.url == "https://example.com/webhook"
        assert config.active is True

    def test_unregister_webhook(self):
        """Webhookを登録解除できること."""
        mgr = WebhookManager()
        config = mgr.register("org-1", "https://example.com/webhook")
        assert mgr.unregister(config.id) is True
        assert len(mgr.list_webhooks("org-1")) == 0

    def test_list_webhooks(self):
        """Webhook一覧が取得できること."""
        mgr = WebhookManager()
        mgr.register("org-1", "https://a.com/hook")
        mgr.register("org-1", "https://b.com/hook")
        mgr.register("org-2", "https://c.com/hook")

        hooks = mgr.list_webhooks("org-1")
        assert len(hooks) == 2

    def test_prepare_delivery(self):
        """Webhook配信が準備できること."""
        mgr = WebhookManager()
        mgr.register("org-1", "https://example.com/hook", events=["incident.created"])

        deliveries = mgr.prepare_delivery(
            "org-1",
            "incident.created",
            {"title": "test incident"},
        )
        assert len(deliveries) == 1
        assert deliveries[0]["url"] == "https://example.com/hook"
        assert "X-JPGovAI-Signature" in deliveries[0]["headers"]

    def test_event_filtering(self):
        """イベントフィルタリングが動作すること."""
        mgr = WebhookManager()
        mgr.register("org-1", "https://a.com/hook", events=["incident.created"])
        mgr.register("org-1", "https://b.com/hook", events=["assessment.completed"])

        deliveries = mgr.prepare_delivery(
            "org-1", "incident.created", {},
        )
        assert len(deliveries) == 1
        assert deliveries[0]["url"] == "https://a.com/hook"

    def test_wildcard_events(self):
        """ワイルドカードイベントが動作すること."""
        mgr = WebhookManager()
        mgr.register("org-1", "https://a.com/hook", events=["*"])

        deliveries = mgr.prepare_delivery("org-1", "any.event", {})
        assert len(deliveries) == 1


class TestResponseBuilders:
    """レスポンスビルダーのテスト."""

    def test_build_assessment_response(self):
        """診断結果レスポンスが構築できること."""
        data = {
            "id": "test-id",
            "organization_id": "org-1",
            "overall_score": 2.5,
            "maturity_level": 3,
            "category_scores": [],
            "timestamp": "2026-01-01T00:00:00Z",
        }
        resp = build_assessment_response(data)
        assert resp["id"] == "test-id"
        assert resp["overall_score"] == 2.5

    def test_build_compliance_score_response(self):
        """準拠スコアレスポンスが構築できること."""
        resp = build_compliance_score_response(
            "org-1",
            meti_score=2.5,
            iso_score=2.0,
            act_score=1.8,
            overall_rate=0.75,
        )
        assert resp["organization_id"] == "org-1"
        assert resp["scores"]["meti_guideline"] == 2.5
        assert resp["overall_compliance_rate"] == 0.75


class TestSingletons:
    """シングルトンのテスト."""

    def test_get_api_key_manager(self):
        """シングルトンが取得できること."""
        mgr = get_api_key_manager()
        assert isinstance(mgr, APIKeyManager)
        assert get_api_key_manager() is mgr

    def test_get_rate_limiter(self):
        """シングルトンが取得できること."""
        limiter = get_rate_limiter()
        assert isinstance(limiter, RateLimiter)

    def test_get_webhook_manager(self):
        """シングルトンが取得できること."""
        mgr = get_webhook_manager()
        assert isinstance(mgr, WebhookManager)

    def test_reset(self):
        """リセットが動作すること."""
        mgr1 = get_api_key_manager()
        reset_public_api()
        mgr2 = get_api_key_manager()
        assert mgr1 is not mgr2
