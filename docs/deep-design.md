# JPGovAI 作り込み設計書 — 生き残るプロダクトへの道

**作成日: 2026-03-25**
**ステータス: 戦略設計（実装前）**

---

## 1. 現状分析（コードベースの弱点）

### 1.1 コードベースから読み取れる実装レベル

現在のJPGovAIは以下のコンポーネントで構成される:

| コンポーネント | ファイル | 実装レベル | 評価 |
|--------------|--------|----------|------|
| 自己診断（25問） | `app/services/assessment.py` | 完成 | スコア計算ロジックは堅実。ただしスコアは単純平均で重み付けなし |
| ギャップ分析 | `app/services/gap_analysis.py` | 完成 | AI改善提案あり（Anthropic API連携）。ただしハードコードされた改善アクション |
| ISO 42001チェック | `app/services/iso_check.py` | 完成 | METIスコアからの推定。独立したISO固有の評価ロジックなし |
| リスクアセスメント | `app/services/risk_assessment.py` | 完成 | EU AI Act準拠。10問のYes/No形式 |
| ポリシー生成 | `app/services/policy_generator.py` | 完成 | **テンプレートの穴埋め**。組織固有の状況を反映しない |
| エビデンス管理 | `app/services/evidence.py` | 骨格のみ | **ファイル保存はシミュレーション**。メタデータ登録のみ |
| タスク管理 | `app/services/task_manager.py` | 完成 | カンバンボード。ただし期限リマインダーなし、通知なし |
| 監査証跡 | `app/services/audit_trail.py` | 完成 | SHA-256ハッシュチェーン+Merkle Tree。技術的には堅実 |
| レポート生成 | `app/services/report_gen.py` | 完成 | **日本語フォント未対応**。Helveticaで出力 |
| ダッシュボード | `app/services/dashboard.py` | 完成 | 3規制のスナップショット。**時系列データなし** |
| 認証 | `app/auth.py` | 完成 | 自前JWT。**組織×ユーザーの紐付けなし（シングルユーザー前提）** |
| DB | `app/db/database.py` | SQLite | **本番運用に不適**。マルチテナント非対応 |
| UI | `ui/streamlit_app.py` | プロトタイプ | **認証なし**でAPI叩いてる。Authヘッダー未送信 |

### 1.2 「これではコモディティ化する」ポイント

**致命的弱点1: ワンショット診断で終わる**
- 診断→ギャップ分析→レポート出力で完結。**顧客が戻ってくる理由がない**
- 競合が同じ25問の診断ツールを1週間で作れる（AIガバナンス協会のナビが先行事例）
- **解約したら何も失わない** = スイッチングコストがゼロ

**致命的弱点2: データが蓄積しない**
- 各企業のデータは独立。**他社のデータから学ぶ仕組みがない**
- 業界ベンチマークが不在。「自社のLevel 2は業界平均と比べてどうか」が不明
- 使えば使うほどAIが賢くなる仕組みがない → **ネットワーク効果なし**

**致命的弱点3: 日常業務に組み込まれない**
- 四半期に1回の診断ツール。**月額課金する理由が弱い**
- 承認ワークフロー、定期レビュー、インシデント記録など日常運用機能がゼロ
- Slack/Teams連携なし。カレンダー連携なし。人はJPGovAIを開かない

**致命的弱点4: チーム機能がない**
- `app/auth.py`: ユーザーと組織の紐付けがない。ロール管理がない
- 1人で使うツールは解約が容易。**複数人が使うツールは外しにくい**
- 上司が承認し、部下が実行し、監査人がレビューする — この流れが作れない

**致命的弱点5: 規制の深さが表面的**
- `app/guidelines/meti_v1_1.py`: 要件の「タイトル」と「説明」のみ
- ガイドラインの「行間」がない。パブリックコメントの回答、経産省の意図、実務での解釈がない
- ISO 42001認証取得の実務手順（審査プロセス、審査員が見るポイント）がない
- **深い専門性なしでは「チェックリストアプリ」止まり**

### 1.3 技術的負債

| 項目 | 現状 | 問題 |
|------|------|------|
| DB | SQLite（`sqlite:///./jpgov_ai.db`） | マルチプロセス不可。本番運用不可 |
| 認証 | 自前JWT + SQLiteユーザーDB | 組織-ユーザー紐付けなし。ロールなし |
| マルチテナント | 非対応 | `organization_id`はあるがアクセス制御なし |
| ファイルストレージ | ローカル `uploads/` | S3等のクラウドストレージ未対応 |
| 非同期処理 | なし | レポート生成など重い処理が同期実行 |
| テスト | ユニットテスト18ファイル | 統合テスト・E2Eテストなし |
| UI | Streamlit | SPA化が必要。認証フロー未実装 |

---

## 2. モートA: データ飛び車輪（Proprietary Data Flywheel）

### 2.1 なぜこれが必要か

- **これがないとどうなるか**: JPGovAIはただのチェックリストアプリ。誰でもコピーできる。顧客が100社になっても1000社になっても、1社目と同じ体験しか提供できない
- **これがあるとどうなるか**: 顧客が増えるほどAIが賢くなり、ベンチマークが正確になり、新規顧客の体験が良くなる。**競合が追いつけない参入障壁**ができる

### 2.2 設計: 匿名化集約データパイプライン

```
顧客Aの診断データ
顧客Bの診断データ     →  匿名化エンジン  →  集約データストア  →  業界別ベンチマーク
顧客Cの診断データ                                              →  改善パターンDB
顧客Dの診断データ                                              →  予測モデル
```

#### コンポーネント1: 匿名化エンジン

**新規ファイル**: `app/services/anonymization.py`

```python
# 個社を特定できない形でデータを集約する
# - organization_id → ハッシュ化（元データを復元不可に）
# - industry + size + ai_role → 属性グループ化
# - 個別スコア → 範囲にバケット化（例: 2.3 → "2.0-2.5"）
# - 5社未満のセグメントはデータ出力しない（k-anonymity, k>=5）
```

責務:
- 診断データの匿名化（k-anonymity保証）
- 差分プライバシーノイズの付加（epsilon=1.0）
- 集約データストアへの書き込み
- 顧客のオプトイン/アウト管理

#### コンポーネント2: 業界別ベンチマーク生成

**新規ファイル**: `app/services/benchmark.py`

```python
class IndustryBenchmark:
    industry: str           # "金融", "IT・通信", etc.
    size_bucket: str        # "small", "medium", "large", "enterprise"
    sample_count: int       # ベンチマーク算出に使った企業数
    avg_overall_score: float
    avg_maturity_level: float
    category_benchmarks: dict[str, CategoryBenchmark]
    percentile_thresholds: dict[int, float]  # {25: 1.2, 50: 2.0, 75: 2.8}
    top_improvement_areas: list[str]         # この業界で最も改善が多い領域
    updated_at: str
```

API:
- `GET /api/benchmark/{industry}` — 業界別ベンチマーク取得
- `GET /api/benchmark/{industry}/my-position?assessment_id=xxx` — 自社の業界内ポジション

UI表示例:
```
あなたの成熟度: Level 2 (スコア 1.8)
金融業界の平均: Level 2.3 (スコア 2.1)
あなたの業界内順位: 下位35%

最も差がある領域:
  C05 セキュリティ: あなた 1.2 / 業界平均 2.8 (差: -1.6)
  C04 プライバシー: あなた 1.5 / 業界平均 2.5 (差: -1.0)
```

#### コンポーネント3: 改善パターン学習

**新規ファイル**: `app/services/pattern_learning.py`

```python
class ImprovementPattern:
    """「この状態からこうすると改善できた」パターン."""
    from_state: dict[str, float]    # 改善前のカテゴリ別スコア
    to_state: dict[str, float]      # 改善後のカテゴリ別スコア
    actions_taken: list[str]        # 実施したアクション（タスクの完了履歴から）
    duration_days: int              # 改善にかかった期間
    industry: str
    size: str
```

仕組み:
- 時系列データ（2回目以降の診断）から改善パターンを抽出
- 「金融業の中規模企業がLevel 2→3に上がるとき、最も効果的だったアクション」を特定
- 新規顧客への改善提案に、実績データに基づくレコメンデーションを付与

#### コンポーネント4: 時系列追跡

**新規ファイル**: `app/services/timeline.py`

```python
class MaturityTimeline:
    organization_id: str
    snapshots: list[TimelineSnapshot]  # 時系列のスコア推移

class TimelineSnapshot:
    assessment_id: str
    timestamp: str
    overall_score: float
    maturity_level: int
    category_scores: dict[str, float]
    delta_from_previous: float  # 前回比
```

API:
- `GET /api/timeline/{organization_id}` — 成熟度推移データ
- `GET /api/timeline/{organization_id}/trend` — トレンド分析（改善速度、予測）

UI表示例:
```
成熟度推移（過去12ヶ月）:
  2025-06: Level 1.8
  2025-09: Level 2.1 (+0.3)
  2025-12: Level 2.4 (+0.3)
  2026-03: Level 2.7 (+0.3)
  予測: 2026-09にLevel 3.0到達見込み
```

### 2.3 飛び車輪の動作

```
                ┌────────────────────────┐
                │  顧客が診断を実行      │
                └──────────┬─────────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │  匿名化して集約DB蓄積   │
                └──────────┬─────────────┘
                           │
                           ▼
          ┌────────────────────────────────────┐
          │  業界ベンチマーク精度が上がる         │
          │  改善パターンの母数が増える            │
          │  AI改善提案の根拠が強化される          │
          └────────────────┬───────────────────┘
                           │
                           ▼
          ┌────────────────────────────────────┐
          │  新規顧客の初回体験が良くなる          │
          │  「業界平均との比較」ができるようになる │
          └────────────────┬───────────────────┘
                           │
                           ▼
          ┌────────────────────────────────────┐
          │  より多くの顧客が利用する              │
          └────────────────┬───────────────────┘
                           │
                           └──→ 最初に戻る（ループ）
```

### 2.4 実装上の制約

- **k-anonymity (k>=5)**: 同一セグメントに5社以上いないとベンチマークを表示しない
- **オプトイン**: 顧客は「匿名データの集約利用」に明示的に同意する必要がある
- **差分プライバシー**: 集約データにノイズを加え、個社データの推測を防ぐ
- **データ削除権**: 顧客が退会時にデータ削除を要求できる（匿名化済みデータは除外可能）

### 2.5 DB設計追加

**新規テーブル**: `anonymized_snapshots`

```sql
CREATE TABLE anonymized_snapshots (
    id TEXT PRIMARY KEY,
    anonymized_org_hash TEXT NOT NULL,  -- SHA-256(org_id + salt)
    industry TEXT NOT NULL,
    size_bucket TEXT NOT NULL,
    ai_role TEXT NOT NULL,
    overall_score REAL,
    maturity_level INTEGER,
    category_scores_json TEXT,  -- {category_id: score}
    snapshot_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_anon_industry ON anonymized_snapshots(industry, size_bucket);
```

**新規テーブル**: `improvement_patterns`

```sql
CREATE TABLE improvement_patterns (
    id TEXT PRIMARY KEY,
    anonymized_org_hash TEXT NOT NULL,
    industry TEXT NOT NULL,
    size_bucket TEXT NOT NULL,
    from_score REAL,
    to_score REAL,
    delta REAL,
    duration_days INTEGER,
    actions_taken_json TEXT,  -- タスク完了履歴（匿名化済み）
    created_at TEXT NOT NULL
);
```

---

## 3. モートB: ワークフロー所有（Workflow Ownership）

### 3.1 なぜこれが必要か

- **これがないとどうなるか**: JPGovAIは「四半期に1回開くツール」。月額課金する理由がない。顧客はExcelに戻る
- **これがあるとどうなるか**: JPGovAIが「毎日開くもの」になる。承認フロー、定期レビュー、インシデント記録がJPGovAI上で動くため、**解約すると業務が止まる**

### 3.2 設計: 日常運用ワークフロー

#### ワークフロー1: 定期レビューサイクル

**新規ファイル**: `app/services/review_cycle.py`

```python
class ReviewCycle:
    """定期レビューサイクルの管理."""
    id: str
    organization_id: str
    cycle_type: str          # "quarterly" / "semi_annual" / "annual"
    target_categories: list[str]  # レビュー対象カテゴリ
    reviewer_ids: list[str]  # レビュアー
    approver_id: str         # 承認者
    status: str              # "scheduled" / "in_review" / "pending_approval" / "approved"
    scheduled_date: str
    due_date: str
    completed_date: str | None
    findings: list[ReviewFinding]
    previous_cycle_id: str | None  # 前回サイクルへのリンク
```

フロー:
```
定期レビュースケジュール設定（四半期ごと）
    │
    ├── リマインダー通知（2週間前、1週間前、当日）
    │
    ▼
レビュアーが各カテゴリの現状を更新
    │
    ├── エビデンスの更新（有効期限切れの確認）
    ├── 前回からの変更点の記録
    ├── 新たなリスクの報告
    │
    ▼
承認者がレビュー結果を承認
    │
    ├── 承認 → 次回サイクルをスケジュール
    ├── 差戻し → レビュアーに再実施を依頼
    │
    ▼
承認完了 → 監査証跡に記録 → 成熟度スコア更新
```

#### ワークフロー2: 承認ワークフロー

**新規ファイル**: `app/services/approval_workflow.py`

```python
class ApprovalRequest:
    """承認リクエスト."""
    id: str
    organization_id: str
    request_type: str       # "policy_change" / "risk_acceptance" / "evidence_approval"
    requester_id: str
    approver_ids: list[str]  # 承認者リスト（順序付き or 並列）
    approval_type: str      # "sequential" / "parallel" / "any_one"
    status: str             # "pending" / "approved" / "rejected" / "expired"
    target_resource_type: str
    target_resource_id: str
    description: str
    attachments: list[str]
    approvals: list[ApprovalAction]  # 各承認者のアクション履歴
    deadline: str
    created_at: str

class ApprovalAction:
    approver_id: str
    action: str     # "approve" / "reject" / "request_change"
    comment: str
    timestamp: str
```

適用場面:
- ポリシー変更 → ガバナンス責任者の承認が必要
- リスク受容 → CAIO/CROの承認が必要
- エビデンスの妥当性 → 監査担当者の承認が必要
- 改善タスクの完了 → レビュアーの確認が必要

#### ワークフロー3: インシデント管理

**新規ファイル**: `app/services/incident_management.py`

```python
class AIIncident:
    """AIインシデント記録."""
    id: str
    organization_id: str
    title: str
    description: str
    severity: str           # "critical" / "high" / "medium" / "low"
    incident_type: str      # "bias" / "security" / "privacy" / "safety" / "quality" / "other"
    affected_system: str    # 影響を受けたAIシステム名
    detected_at: str
    detected_by: str
    root_cause: str
    impact_assessment: str
    corrective_actions: list[str]
    preventive_actions: list[str]
    status: str             # "detected" / "investigating" / "mitigating" / "resolved" / "closed"
    related_requirements: list[str]  # 影響するMETI/ISO要件
    timeline: list[IncidentEvent]    # 対応タイムライン
    lessons_learned: str
    regulatory_notification_required: bool
    regulatory_notification_sent: bool
```

この機能が生む価値:
- インシデント記録が蓄積 → エビデンスとして監査に活用
- 影響する要件に自動リンク → ギャップ分析に反映
- 対応タイムラインが監査証跡に記録 → 改竄防止

#### ワークフロー4: 監査対応パッケージ自動生成

**新規ファイル**: `app/services/audit_package.py`

```python
class AuditPackage:
    """外部監査用エビデンスパッケージ."""
    id: str
    organization_id: str
    audit_type: str  # "iso42001" / "internal" / "regulatory"
    target_framework: str
    generated_at: str
    sections: list[AuditSection]

class AuditSection:
    requirement_id: str
    requirement_title: str
    compliance_status: str
    evidence_list: list[EvidenceRecord]
    review_history: list[ReviewRecord]  # レビューサイクルの履歴
    incident_history: list[AIIncident]  # 関連インシデント
    policy_documents: list[PolicyDocument]
    approval_records: list[ApprovalRequest]
    gap_history: list[GapSnapshot]  # 過去のギャップ推移
```

仕組み:
- 監査員が「ISO 42001の条項6.1に対するエビデンスを見せて」と言ったとき
- ボタン一つでその条項に対する全エビデンス（方針文書、レビュー記録、インシデント対応記録、承認記録）を一括出力
- **これがないと**: 担当者が各所からファイルを集める作業が発生（1-2週間）
- **これがあると**: 30秒で出力。監査対応コストが劇的に減少

### 3.3 チーム・ロール機能

**新規ファイル**: `app/services/team.py`

```python
class OrganizationMember:
    user_id: str
    organization_id: str
    role: str  # "owner" / "admin" / "governance_officer" / "reviewer" / "contributor" / "viewer"
    permissions: list[str]
    invited_at: str
    joined_at: str

class Role:
    role_id: str
    name: str
    permissions: list[str]  # ["assessment.create", "policy.approve", "evidence.upload", ...]
```

ロール設計:
| ロール | できること |
|--------|----------|
| owner | 全権限 + メンバー管理 + 契約管理 |
| admin | 全権限 + メンバー管理 |
| governance_officer | 診断実行、ポリシー承認、レビュー承認 |
| reviewer | レビュー実施、エビデンス検証 |
| contributor | タスク更新、エビデンスアップロード |
| viewer | 閲覧のみ |

### 3.4 外部連携

**新規ファイル**: `app/services/integrations.py`

| 連携先 | 機能 | 実装優先度 |
|--------|------|----------|
| Slack | レビューリマインダー、承認通知、インシデントアラート | P0 |
| Microsoft Teams | 同上 | P0 |
| Google Calendar | 定期レビュースケジュールの自動登録 | P1 |
| Outlook Calendar | 同上 | P1 |
| Jira | 改善タスクの双方向同期 | P2 |
| Google Drive / SharePoint | エビデンスファイルの直接参照 | P2 |

Slack連携の具体例:
```
#ai-governance チャンネル
───────────────────────────────
🔔 JPGovAI: 四半期レビューの期限が近づいています
期限: 2026-03-31 | レビュー対象: C02 安全性, C05 セキュリティ
担当: @田中, @佐藤
[レビューを開始する]  [後でリマインド]
───────────────────────────────

✅ JPGovAI: ポリシー変更が承認されました
「AI利用ポリシー v2.1」が @鈴木部長 により承認されました
[変更内容を確認する]
───────────────────────────────

🚨 JPGovAI: AIインシデント報告
重要度: HIGH | 種別: bias
チャットボットが特定年齢層に対して不適切な応答を生成
[詳細を確認する]  [対応を開始する]
```

### 3.5 「解約すると何が起きるか」の設計

JPGovAIを解約した場合に顧客が失うもの:

| 失うもの | インパクト |
|---------|----------|
| 過去の全診断履歴と成熟度推移 | 監査時に提示できない |
| レビューサイクルの履歴 | 継続的改善の証跡がなくなる |
| 承認フローの記録 | ガバナンスの意思決定証跡が消失 |
| インシデント対応記録 | 規制当局への報告に使えない |
| エビデンス管理の体系 | ファイルがバラバラになる |
| 監査証跡（暗号学的保証付き） | 改竄防止の証拠能力が消失 |
| 業界ベンチマークへのアクセス | 自社の相対位置がわからなくなる |
| AI改善提案のパーソナライズ | 汎用的な提案しか得られない |

**このリストが長いほど、スイッチングコストが高い = 解約されにくい**

---

## 4. モートC: 規制×日本語の深い専門性

### 4.1 なぜこれが必要か

- **これがないとどうなるか**: 「チェックリスト」はOSSでもExcelでも作れる。VerifyWiseに日本語モジュールを追加されたら終わり
- **これがあるとどうなるか**: JPGovAIでしか得られない専門的知見がある。コンサルに聞くか、JPGovAIを使うかの二択になる

### 4.2 設計: 規制ナレッジベース

**新規ファイル**: `app/services/knowledge_base.py`

```python
class RegulatoryKnowledge:
    """規制の深い知見."""
    id: str
    regulation: str          # "meti_v1.1" / "iso42001" / "ai_promotion_act"
    requirement_id: str      # 対応する要件ID
    knowledge_type: str      # "interpretation" / "practice" / "case_study" / "audit_point"
    title: str
    content: str             # Markdown形式
    source: str              # 出典（パブコメ回答、審査事例等）
    source_url: str
    industry_relevance: list[str]  # 関連業種
    created_at: str
    updated_at: str

class AuditPoint:
    """ISO 42001審査で見られるポイント."""
    requirement_id: str
    what_auditor_checks: str    # 審査員が確認すること
    common_findings: list[str]  # よくある不適合事項
    evidence_expected: list[str]  # 期待されるエビデンス
    best_practices: list[str]   # ベストプラクティス
    sgs_specific: str           # SGSジャパン固有の傾向
    tuv_specific: str           # テュフラインランド固有の傾向
```

### 4.3 具体的なナレッジコンテンツ

#### 4.3.1 METI AI事業者ガイドラインの「行間を読む」解釈ガイド

現在の `meti_v1_1.py` は要件のタイトルと説明のみ。以下を追加:

| 要件 | 現在の説明 | 追加すべき「行間」 |
|------|----------|----------------|
| C01-R02 人間の関与 | 「人間が確認・判断できるプロセスを整備」 | **実務ポイント**: 全AIシステムに必要ではない。ガイドライン本文p.18「リスクの程度に応じた」関与が求められる。社内業務効率化の低リスクAIにHuman-in-the-Loopは過剰対応。**経産省パブコメ回答No.34参照** |
| C02-R01 リスクアセスメント | 「定期的に実施」 | **実務ポイント**: 「定期的」の具体的な頻度は定められていないが、パブコメ回答では「重大変更時と少なくとも年1回」が示唆されている。ISO 42001認証では四半期ごとが推奨される |
| C04-R02 PIA | 「プライバシー影響評価を実施」 | **実務ポイント**: PIAの実施義務は「高リスク」な場合。ガイドラインp.29-30。個人情報を一切扱わないAIシステムには不要。ただしISO 42001のAnnex Bでは全AIシステムに影響評価を推奨 |
| C06-R01 AI利用の明示 | 「利害関係者に適切に開示」 | **実務ポイント**: AI推進法第12条「透明性の確保」との関連。2025年パブコメでは「AI利用の表示方法は事業者の判断に委ねる」とされた。ただしEU AI Act Art.50ではAI生成コンテンツの明示が義務 |

**新規ファイル**: `app/guidelines/meti_interpretation.py`

各要件に対する解釈ガイドを構造化データとして保持。

#### 4.3.2 ISO 42001認証取得の実務手順ガイド

**新規ファイル**: `app/knowledge/iso42001_certification_guide.py`

```python
CERTIFICATION_PROCESS = {
    "phases": [
        {
            "phase": 1,
            "name": "ギャップ分析と計画策定",
            "duration": "1-2ヶ月",
            "tasks": [
                "現状のAIガバナンス体制の棚卸し",
                "ISO 42001の全要求事項とのギャップ特定（← JPGovAIが自動化）",
                "是正計画の策定と優先順位付け",
                "プロジェクト体制の構築（AIガバナンス委員会の設立）",
            ],
            "jpgovai_value": "ギャップ分析を自動実行。手動では2-4週間かかる作業を30分に短縮",
        },
        {
            "phase": 2,
            "name": "AIMS（AIマネジメントシステム）の構築",
            "duration": "3-6ヶ月",
            "tasks": [
                "AIポリシーの策定（← JPGovAIのポリシー生成機能）",
                "リスクアセスメント手順の確立",
                "AIシステムインベントリの作成",
                "影響評価プロセスの設計",
                "インシデント対応手順の整備",
                "教育訓練プログラムの策定",
                "内部監査計画の策定",
            ],
            "jpgovai_value": "ポリシーテンプレート自動生成。エビデンス管理で文書を体系化",
        },
        {
            "phase": 3,
            "name": "運用と内部監査",
            "duration": "3ヶ月以上",
            "tasks": [
                "AIMSの運用開始",
                "内部監査の実施（最低1回）",
                "マネジメントレビューの実施",
                "是正措置の実施と有効性確認",
            ],
            "jpgovai_value": "定期レビューサイクルが運用の証跡に。監査証跡が改竄防止で信頼性確保",
        },
        {
            "phase": 4,
            "name": "認証審査",
            "duration": "2-4週間",
            "tasks": [
                "Stage 1審査（文書審査）",
                "Stage 2審査（実地審査）",
                "不適合の是正（あれば）",
                "認証登録",
            ],
            "jpgovai_value": "監査パッケージ自動生成で審査対応コストを80%削減",
            "audit_bodies": {
                "sgs_japan": {
                    "name": "SGSジャパン",
                    "accredited_since": "2026-01",
                    "focus_areas": "リスクアセスメントの具体性、エビデンスの充足度",
                },
                "tuv_rheinland_japan": {
                    "name": "テュフラインランドジャパン",
                    "accredited_since": "2026-01",
                    "focus_areas": "プロセスの継続性、内部監査の実効性",
                },
            },
        },
    ],
}
```

#### 4.3.3 業種別の具体的対応ガイド

現在の `industry_specific.py` を大幅に拡張:

**金融業の例**:
```python
FINANCIAL_DEEP_GUIDE = {
    "C02-R01": {  # リスクアセスメント
        "industry_context": (
            "金融庁AIディスカッションペーパーv1.1（2026年3月）では、"
            "金融機関のAIリスクを以下の5カテゴリで分類:\n"
            "1. モデルリスク（精度劣化、ドリフト）\n"
            "2. データリスク（品質、バイアス、プライバシー）\n"
            "3. オペレーショナルリスク（障害、誤操作）\n"
            "4. コンダクトリスク（不公正取引、優越的地位の濫用）\n"
            "5. サイバーリスク（敵対的攻撃、データ漏洩）"
        ),
        "specific_actions": [
            "AIモデルの「インベントリ」を作成し、リスクレベルを分類する",
            "高リスクモデル（与信判断、不正検知等）には独立したモデル検証を実施する",
            "金融庁検査でのAI関連の質問に対する回答準備書を整備する",
        ],
        "case_study": (
            "事例: メガバンクA社はAI与信モデルの導入時、モデルリスク管理態勢として"
            "「三線防御」（1線: 開発部門、2線: リスク管理部門、3線: 内部監査部門）を"
            "構築。金融庁検査で「ベストプラクティス」と評価された。"
        ),
    },
}
```

#### 4.3.4 規制変更の即時対応エンジン

**新規ファイル**: `app/services/regulatory_monitor.py`

```python
class RegulatoryUpdate:
    """規制変更情報."""
    id: str
    regulation: str
    update_type: str     # "new_law" / "amendment" / "guideline_update" / "enforcement" / "public_comment"
    title: str
    summary: str
    impact_assessment: str    # JPGovAIの要件への影響
    affected_requirements: list[str]  # 影響する要件ID
    effective_date: str
    source_url: str
    published_at: str
    actions_required: list[str]  # 顧客がすべきこと
```

仕組み:
- 経産省、金融庁、IPA等のRSSフィード/ページを定期監視
- AI推進法の政令・省令が出たら即座に要件を更新
- 顧客にメール/Slack通知: 「AI推進法の施行規則が公布されました。あなたの組織への影響: ...」

---

## 5. モートD: Citadel AI連携

### 5.1 なぜこれが必要か

- **これがないとどうなるか**: JPGovAIは「管理」だけ。実際のAIモデルの品質・安全性は別途管理が必要。「ガバナンスはJPGovAIで管理してるけど、モデルの監視はどうする？」に答えられない
- **これがあるとどうなるか**: 「Citadel AI + JPGovAI = AIガバナンスのフルスタック」が実現。技術レイヤー（モデル監視）とマネジメントレイヤー（ガバナンス管理）の両方をカバー

### 5.2 レイヤー分離と連携ポイント

```
┌─────────────────────────────────────────────────────────┐
│ マネジメントレイヤー (JPGovAI)                            │
│                                                          │
│  方針策定 ─ リスク評価 ─ ギャップ管理 ─ 監査対応         │
│  承認フロー ─ インシデント管理 ─ 改善タスク               │
│  エビデンス管理 ─ レポート生成 ─ 規制対応                 │
│                                                          │
│            ↕ API連携（エビデンス自動取り込み）            │
│                                                          │
│ 技術レイヤー (Citadel AI)                                │
│                                                          │
│  モデル品質監視 ─ ドリフト検出 ─ バイアス検出             │
│  敵対的攻撃検知 ─ 説明可能性 ─ パフォーマンス監視        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.3 連携設計

**新規ファイル**: `app/services/citadel_integration.py`

```python
class CitadelConnector:
    """Citadel AIとの連携コネクタ."""

    def import_monitoring_report(self, citadel_report: dict) -> list[EvidenceRecord]:
        """Citadel AIの監視レポートをエビデンスとしてインポート.

        マッピング:
        - Citadelのバイアス検出結果 → C03-R01 (バイアス評価の実施) のエビデンス
        - Citadelのドリフト検出結果 → C02-R01 (リスクアセスメント) のエビデンス
        - Citadelの敵対的攻撃テスト → C05-R01 (セキュリティ対策) のエビデンス
        - Citadelの説明可能性レポート → C06-R02 (判断根拠の説明) のエビデンス
        - Citadelのモデルカード → C06-R03 (技術情報の文書化) のエビデンス
        """

    def sync_incidents(self, citadel_alerts: list[dict]) -> list[AIIncident]:
        """Citadel AIのアラートをインシデントとして取り込み.

        - Citadelが異常を検知 → JPGovAIにインシデント自動登録
        - 関連する要件に自動リンク
        - 対応ワークフローを自動起動
        """

    def generate_evidence_from_monitoring(
        self, system_id: str, period: str
    ) -> AuditPackage:
        """Citadel AIの定期監視データからエビデンスパッケージを生成.

        ISO 42001審査用に:
        - 「継続的なモデル監視を行っている」証拠
        - 「バイアスの定期的な評価を行っている」証拠
        - 「セキュリティテストを定期的に行っている」証拠
        をCitadel AIのデータから自動生成する。
        """
```

### 5.4 Citadel AIのデータ→JPGovAIの要件マッピング

| Citadel AI機能 | JPGovAI METI要件 | ISO 42001要件 | エビデンスとしての価値 |
|---------------|-----------------|-------------|---------------------|
| モデル品質スコア | C02-R02 学習データ品質 | ISO-6.1.2 | モデルの品質が管理されている証拠 |
| バイアス検出 | C03-R01 バイアス評価 | ISO-8.4 | 公平性の定期的な評価の証拠 |
| データドリフト検出 | C02-R01 リスクアセスメント | ISO-8.2 | 継続的なリスクモニタリングの証拠 |
| 敵対的攻撃テスト | C05-R01 セキュリティ | ISO-8.3 | セキュリティ対策の証拠 |
| 説明可能性レポート | C06-R02 判断根拠の説明 | ISO-7.4 | 透明性確保の証拠 |
| モデルカード | C06-R03 技術情報文書化 | ISO-7.5 | 文書化の証拠 |
| アラート履歴 | C05-R03 インシデント対応 | ISO-10.1 | インシデント検知体制の証拠 |

### 5.5 ビジネス上の意味

- **JPGovAI単体**: マネジメントの「箱」だけ。中身（実際の監視データ）は手動入力
- **Citadel AI単体**: 技術的な監視データはあるが、「それがガバナンス上何を意味するか」の変換が必要
- **JPGovAI + Citadel AI**: 技術データが自動的にガバナンスエビデンスに変換される。**監査対応が自動化される**

---

## 6. 収益モデル深化

### 6.1 現状の問題

現在の `pricing-strategy.md` は価格表を定義しているが、**リテンション（解約防止）の仕組みが弱い**。

- Free → Starter転換: 「改善アクションの詳細」が有料。ただしこれは1回見れば十分
- Starter → Professional: 「監査証跡」が有料。ただし監査がない企業には価値不明
- **月額課金の正当化**: 毎月何が得られるのかが不明確

### 6.2 改善された収益モデル

#### Tier再設計

| Plan | Free | Starter ¥29,800/月 | Professional ¥59,800/月 | Enterprise ¥98,000/月 |
|------|------|-----------|-------------|------------|
| **自己診断** | 年1回 | 無制限 | 無制限 | 無制限 |
| **ギャップ分析** | サマリーのみ | 全文 | 全文+AI提案 | 全文+AI提案+カスタム |
| **業界ベンチマーク** | なし | 基本（平均値のみ） | 詳細（パーセンタイル）| 詳細+カスタムピアグループ |
| **成熟度推移** | なし | 過去3回分 | 無制限 | 無制限 |
| **ポリシー生成** | なし | 3種類 | 全10種類 | 全10種類+カスタム |
| **エビデンス管理** | なし | 10ファイル | 無制限 | 無制限 |
| **定期レビュー** | なし | なし | 四半期サイクル | カスタムサイクル |
| **承認ワークフロー** | なし | なし | 基本 | 高度（多段階承認）|
| **インシデント管理** | なし | なし | 基本 | 高度（SLA連携）|
| **監査パッケージ** | なし | なし | 自動生成 | 自動生成+カスタム |
| **監査証跡** | なし | なし | SHA-256チェーン | SHA-256+Merkle Tree |
| **規制変更アラート** | なし | メール（月次） | メール+Slack（即時）| 即時+影響評価付き |
| **Citadel AI連携** | なし | なし | なし | あり |
| **API** | なし | なし | Read-only | Full CRUD |
| **ユーザー数** | 1 | 5 | 20 | 無制限 |
| **Slack/Teams連携** | なし | なし | あり | あり |
| **SSO/SAML** | なし | なし | なし | あり |

#### リテンションの仕組み

**毎月の価値提供サイクル**:
```
月初:
  └─ 規制変更アラート（今月の変更点のまとめ）
  └─ 業界ベンチマーク更新（前月の集計反映）

月中:
  └─ 定期レビューリマインダー（該当する場合）
  └─ タスク期限リマインダー
  └─ エビデンス有効期限アラート

月末:
  └─ 月次レポート自動生成
     ├─ 今月の改善進捗
     ├─ 業界ベンチマークとの比較変動
     ├─ 未対応タスクのサマリー
     └─ 来月の推奨アクション
```

**解約すると監査証跡が途切れる**:
- JPGovAIの監査証跡は「連続性」が価値
- 2026年1月〜2026年12月の11ヶ月分の証跡があっても、2026年6月に3ヶ月の穴があれば、ISO 42001審査で「継続的なモニタリングを行っている」とは認められない
- **顧客は「途切れさせたくない」から解約しない**

### 6.3 アップセルパス

```
Free（診断）
  │
  ├── 「Level 2です。改善したい」→ Starter
  │
  ▼
Starter（改善アクション）
  │
  ├── 「チームで使いたい」→ Professional
  ├── 「ISO 42001認証を取りたい」→ Professional
  ├── 「金融庁検査に備えたい」→ Professional + 金融業アドオン
  │
  ▼
Professional（ワークフロー）
  │
  ├── 「Citadel AIと連携したい」→ Enterprise
  ├── 「SSO/SAMLが必要」→ Enterprise
  ├── 「API連携したい」→ Enterprise
  │
  ▼
Enterprise（フルプラットフォーム）
```

### 6.4 業種別アドオン

| アドオン | 月額 | 内容 |
|---------|------|------|
| 金融業パック | +¥19,800 | 金融庁DP対応チェック、モデルリスク管理テンプレート、金融検査対応ガイド |
| 医療業パック | +¥19,800 | PMDA AI-SaMD対応、臨床意思決定支援AI特有の要件 |
| 自動車業パック | +¥19,800 | 自動運転AI安全ガイドライン対応 |
| EU対応パック | +¥29,800 | EU AI Act全対応、CE適合性評価支援 |

---

## 7. 開発優先順位

### Phase 1: 基盤整備（0-2ヶ月）— 技術的負債の解消

**目的**: 本番運用に耐える基盤を作る

| 優先度 | タスク | ファイル | 理由 |
|--------|--------|---------|------|
| P0 | PostgreSQL移行 | `app/db/database.py` | SQLiteでは本番運用不可 |
| P0 | マルチテナント対応 | `app/db/database.py`, `app/auth.py` | 組織×ユーザーの紐付け |
| P0 | ロール・権限管理 | 新規: `app/services/team.py` | チーム機能の基盤 |
| P1 | Next.js UI基盤 | 新規: `ui-next/` | Streamlitからの移行開始 |
| P1 | S3エビデンスストレージ | `app/services/evidence.py` | 実ファイルアップロード |

### Phase 2: ワークフロー基盤（2-4ヶ月）— 日常利用の実現

**目的**: 「毎日開くツール」にする

| 優先度 | タスク | ファイル | 理由 |
|--------|--------|---------|------|
| P0 | 時系列追跡 | 新規: `app/services/timeline.py` | 成熟度推移の可視化 |
| P0 | 定期レビューサイクル | 新規: `app/services/review_cycle.py` | 継続利用の核 |
| P0 | Slack連携 | 新規: `app/services/integrations.py` | 通知・リマインダー |
| P1 | 承認ワークフロー | 新規: `app/services/approval_workflow.py` | チーム利用の促進 |
| P1 | インシデント管理 | 新規: `app/services/incident_management.py` | エビデンス蓄積 |
| P2 | Teams連携 | `app/services/integrations.py` | 企業の標準ツール対応 |

### Phase 3: データ飛び車輪（4-6ヶ月）— 競争優位の構築

**目的**: 使うほど賢くなる仕組み

| 優先度 | タスク | ファイル | 理由 |
|--------|--------|---------|------|
| P0 | 匿名化エンジン | 新規: `app/services/anonymization.py` | データ集約の基盤 |
| P0 | 業界ベンチマーク | 新規: `app/services/benchmark.py` | 最大の差別化要素 |
| P1 | 改善パターン学習 | 新規: `app/services/pattern_learning.py` | AI提案の精度向上 |
| P1 | 月次レポート自動生成 | `app/services/report_gen.py` 拡張 | リテンション施策 |
| P2 | 規制変更モニター | 新規: `app/services/regulatory_monitor.py` | 専門性の深化 |

### Phase 4: 専門性の深化（6-9ヶ月）— 参入障壁の構築

**目的**: コンサルに近い価値を提供

| 優先度 | タスク | ファイル | 理由 |
|--------|--------|---------|------|
| P0 | 規制ナレッジベース | 新規: `app/services/knowledge_base.py` | 深い専門性 |
| P0 | METI解釈ガイド | 新規: `app/guidelines/meti_interpretation.py` | ガイドラインの行間 |
| P1 | ISO認証ガイド | 新規: `app/knowledge/iso42001_certification_guide.py` | 実務手順 |
| P1 | 監査パッケージ自動生成 | 新規: `app/services/audit_package.py` | 監査コスト削減 |
| P2 | 金融業ディープガイド | `app/guidelines/industry_specific.py` 拡張 | セクター特化 |

### Phase 5: エコシステム連携（9-12ヶ月）— 市場拡大

**目的**: パートナーとの連携による市場拡大

| 優先度 | タスク | ファイル | 理由 |
|--------|--------|---------|------|
| P1 | Citadel AI連携 | 新規: `app/services/citadel_integration.py` | フルスタック実現 |
| P1 | Public API公開 | `app/main.py` 拡張 | エコシステム構築 |
| P2 | Jira連携 | `app/services/integrations.py` 拡張 | タスク管理統合 |
| P2 | Google Drive/SharePoint連携 | `app/services/integrations.py` 拡張 | エビデンス統合 |

---

## 8. 技術的な実装計画（ファイル単位）

### 8.1 Phase 1: 基盤整備 — 新規・変更ファイル一覧

#### `app/db/database.py` の変更

```
変更内容:
- SQLite → PostgreSQL (asyncpg + SQLAlchemy async)
- マルチテナント対応: 全クエリにorganization_idフィルタ
- Row Level Security (RLS) の設定
- 接続プーリング設定

新規テーブル:
- organization_members (user_id, org_id, role, permissions)
- user_org_invitations (招待管理)
- anonymized_snapshots (匿名化診断データ)
- improvement_patterns (改善パターン)
- review_cycles (定期レビュー)
- approval_requests (承認ワークフロー)
- approval_actions (承認アクション履歴)
- ai_incidents (インシデント記録)
- incident_events (インシデントタイムライン)
- regulatory_updates (規制変更情報)
- knowledge_entries (ナレッジベース)
```

#### `app/auth.py` の変更

```
変更内容:
- 組織×ユーザーの紐付け追加
- ロール・権限チェック関数の追加
- get_current_user → get_current_user_with_org (組織コンテキスト付き)
- 権限デコレータ: @require_permission("assessment.create")

新規関数:
- check_org_permission(user_id, org_id, permission) -> bool
- get_user_role(user_id, org_id) -> str
- invite_member(org_id, email, role) -> Invitation
- accept_invitation(invitation_id, user_id) -> OrganizationMember
```

#### 新規ファイル一覧

| ファイル | 責務 | Phase |
|---------|------|-------|
| `app/services/team.py` | チーム・ロール管理 | 1 |
| `app/services/timeline.py` | 成熟度時系列追跡 | 2 |
| `app/services/review_cycle.py` | 定期レビューサイクル | 2 |
| `app/services/approval_workflow.py` | 承認ワークフロー | 2 |
| `app/services/incident_management.py` | インシデント管理 | 2 |
| `app/services/integrations.py` | 外部連携 (Slack/Teams/Calendar) | 2 |
| `app/services/anonymization.py` | データ匿名化エンジン | 3 |
| `app/services/benchmark.py` | 業界ベンチマーク生成 | 3 |
| `app/services/pattern_learning.py` | 改善パターン学習 | 3 |
| `app/services/regulatory_monitor.py` | 規制変更モニタリング | 3 |
| `app/services/knowledge_base.py` | 規制ナレッジベース | 4 |
| `app/services/audit_package.py` | 監査パッケージ自動生成 | 4 |
| `app/services/citadel_integration.py` | Citadel AI連携 | 5 |
| `app/guidelines/meti_interpretation.py` | METI解釈ガイド | 4 |
| `app/knowledge/iso42001_certification_guide.py` | ISO認証実務ガイド | 4 |
| `app/knowledge/financial_deep_guide.py` | 金融業ディープガイド | 4 |

### 8.2 API設計（新規エンドポイント）

#### Phase 2: ワークフロー系

```
# 定期レビュー
POST   /api/review-cycles                          レビューサイクル作成
GET    /api/review-cycles/{org_id}                  レビューサイクル一覧
PUT    /api/review-cycles/{cycle_id}                レビューサイクル更新
POST   /api/review-cycles/{cycle_id}/findings       所見の追加
POST   /api/review-cycles/{cycle_id}/approve        レビュー承認

# 承認ワークフロー
POST   /api/approvals                               承認リクエスト作成
GET    /api/approvals/{org_id}                       承認リクエスト一覧
POST   /api/approvals/{approval_id}/approve          承認
POST   /api/approvals/{approval_id}/reject           却下
GET    /api/approvals/pending/{user_id}              自分の未承認リスト

# インシデント管理
POST   /api/incidents                               インシデント登録
GET    /api/incidents/{org_id}                       インシデント一覧
PUT    /api/incidents/{incident_id}                  インシデント更新
POST   /api/incidents/{incident_id}/events           イベント追加
POST   /api/incidents/{incident_id}/close            クローズ
```

#### Phase 3: データ飛び車輪系

```
# ベンチマーク
GET    /api/benchmark/{industry}                     業界ベンチマーク
GET    /api/benchmark/{industry}/my-position          自社ポジション

# タイムライン
GET    /api/timeline/{org_id}                        成熟度推移
GET    /api/timeline/{org_id}/trend                  トレンド分析

# 月次レポート
GET    /api/monthly-report/{org_id}                  月次レポート取得
POST   /api/monthly-report/{org_id}/generate         月次レポート生成
```

#### Phase 4: 専門性系

```
# ナレッジベース
GET    /api/knowledge/{requirement_id}               要件の深い知見
GET    /api/knowledge/audit-points/{requirement_id}   審査ポイント
GET    /api/knowledge/certification-guide             認証取得ガイド
GET    /api/knowledge/industry/{industry}/{req_id}    業種別ガイド

# 監査パッケージ
POST   /api/audit-package/generate                   監査パッケージ生成
GET    /api/audit-package/{package_id}               パッケージ取得

# 規制変更
GET    /api/regulatory-updates                       規制変更一覧
GET    /api/regulatory-updates/impact/{org_id}       自社への影響
```

### 8.3 データ移行計画

```
SQLite → PostgreSQL 移行:
1. Alembicマイグレーションスクリプト作成
2. 既存テーブルのスキーマ変換
3. データエクスポート (SQLite → JSON)
4. データインポート (JSON → PostgreSQL)
5. Row Level Security (RLS) ポリシー設定
6. インデックス最適化

新テーブル追加:
- Alembicのバージョン管理で段階的に追加
- Phase 1: organization_members, user_org_invitations
- Phase 2: review_cycles, approval_requests, ai_incidents
- Phase 3: anonymized_snapshots, improvement_patterns
- Phase 4: knowledge_entries, regulatory_updates
```

---

## 付録: 判断基準のまとめ

### 各モートの「これがないとどうなるか / これがあるとどうなるか」

| モート | ないとどうなるか | あるとどうなるか |
|--------|----------------|----------------|
| **データ飛び車輪** | 1000社使っても1社目と同じ体験。コピー容易 | 顧客増加→AI精度向上→体験向上→顧客増加のループ |
| **ワークフロー所有** | 四半期に1回のツール。解約容易 | 毎日使うツール。解約すると業務が止まる |
| **規制専門性** | チェックリストアプリ。OSSで代替可能 | コンサルに聞くかJPGovAIかの二択 |
| **Citadel AI連携** | 管理の「箱」だけ。中身は手動 | 技術+管理のフルスタック。監査が自動化 |
| **収益深化** | 月額課金の正当化が弱い | 毎月の価値提供。解約すると証跡が途切れる |

### 最優先で作るべきもの（Phase 1-2で必須）

1. **PostgreSQL移行 + マルチテナント**: 他の全機能の前提
2. **チーム・ロール機能**: 複数人利用 = スイッチングコスト向上
3. **時系列追跡**: 「前回より改善した」の可視化 = 継続利用動機
4. **定期レビューサイクル + Slack通知**: 日常利用 = 月額課金の正当化
5. **業界ベンチマーク**: 「あなたは業界平均以下」= 改善動機

この5つが揃えば、「チェックリストアプリ」から「AIガバナンス管理プラットフォーム」への脱皮が完了する。
