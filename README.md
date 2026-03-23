# JPGovAI - AI Governance Mark取得支援SaaS

経済産業省・総務省「AI事業者ガイドライン（第1.0版, 2024年4月）」に準拠した
AIガバナンス認証取得を支援するSaaSプロトタイプ。

## 機能

1. **自己診断 (Self-Assessment)**: 25問の質問票でAIガバナンス成熟度を1-5段階で診断
2. **ギャップ分析**: ガイドラインの全28要件に対する充足/部分充足/未充足を可視化、AI改善提案
3. **エビデンス管理**: 各要件に対するエビデンスのアップロード・充足率ダッシュボード
4. **レポート生成**: AI Governance Mark申請用の自己評価レポートをPDF出力
5. **監査証跡**: SHA-256ハッシュチェーン＋Merkle Treeによる改竄防止ログ

## 技術スタック

- **バックエンド**: Python / FastAPI
- **AI**: Anthropic API (Claude) — ギャップ分析・改善提案
- **フロントエンド**: Streamlit
- **DB**: SQLite
- **PDF**: fpdf2

## セットアップ

```bash
# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定（省略時はフォールバック提案を使用）

# APIサーバー起動
uvicorn app.main:app --reload

# 別ターミナルでUI起動
streamlit run ui/streamlit_app.py
```

## テスト

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## ガイドラインカバレッジ

METI AI事業者ガイドライン 10原則:

| ID | 原則 | 要件数 |
|----|------|--------|
| C01 | 人間中心 | 3 |
| C02 | 安全性 | 3 |
| C03 | 公平性 | 3 |
| C04 | プライバシー保護 | 3 |
| C05 | セキュリティ確保 | 3 |
| C06 | 透明性 | 3 |
| C07 | アカウンタビリティ | 4 |
| C08 | 教育・リテラシー | 2 |
| C09 | 公正競争の確保 | 2 |
| C10 | イノベーション | 2 |

## API Endpoints

| Method | Path | 説明 |
|--------|------|------|
| POST | /api/organizations | 組織登録 |
| GET | /api/guidelines/categories | カテゴリ一覧 |
| GET | /api/guidelines/requirements | 要件一覧 |
| GET | /api/guidelines/questions | 質問票一覧 |
| POST | /api/assessment | 自己診断実行 |
| GET | /api/assessment/{id} | 診断結果取得 |
| POST | /api/gap-analysis | ギャップ分析実行 |
| GET | /api/gap-analysis/{id} | ギャップ分析結果取得 |
| POST | /api/evidence | エビデンス登録 |
| GET | /api/evidence/{org_id} | エビデンス一覧 |
| GET | /api/evidence-summary/{org_id} | 充足率サマリー |
| POST | /api/report | レポート生成 |
| GET | /api/audit/events | 監査イベント一覧 |
| GET | /api/audit/verify | チェーン整合性検証 |

## ライセンス

Proprietary
