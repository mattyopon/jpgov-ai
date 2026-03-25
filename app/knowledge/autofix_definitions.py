# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""AutoFix定義: 28要件それぞれに対する自動修復の内容を定義.

各要件に対して以下を定義:
- 生成する文書（ポリシー、チェックリスト、テンプレート、手順書）
- タスクリスト（担当ロール、期限日数、依存関係）
- セルフチェック質問
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentDefinition:
    """自動生成する文書の定義."""

    title: str
    doc_type: str  # policy / checklist / template / procedure
    template: str  # Markdown テンプレート（{org_name} 等のプレースホルダ含む）


@dataclass(frozen=True)
class TaskDefinition:
    """自動生成するタスクの定義."""

    title: str
    description: str
    assignee_role: str  # 担当ロール（例: "AIガバナンス責任者"）
    deadline_days: int  # 基準日から何日以内か
    depends_on: list[int] = field(default_factory=list)  # 同一要件内のタスク順序（0-indexed）


@dataclass(frozen=True)
class SelfCheckQuestion:
    """セルフチェック質問."""

    question: str
    expected_answer: str  # "yes" で対応完了とみなす


@dataclass(frozen=True)
class AutoFixDefinition:
    """1要件に対するAutoFix定義."""

    requirement_id: str
    documents: list[DocumentDefinition] = field(default_factory=list)
    tasks: list[TaskDefinition] = field(default_factory=list)
    self_check_questions: list[SelfCheckQuestion] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 全28要件のAutoFix定義
# ---------------------------------------------------------------------------

AUTOFIX_DEFINITIONS: dict[str, AutoFixDefinition] = {}


def _register(defn: AutoFixDefinition) -> None:
    AUTOFIX_DEFINITIONS[defn.requirement_id] = defn


# ── C01-R01: 人間の尊厳・自律の尊重 ───────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C01-R01",
    documents=[
        DocumentDefinition(
            title="AI利用基本方針",
            doc_type="policy",
            template=(
                "# AI利用基本方針\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 目的\n"
                "本方針は、{org_name}におけるAIの利用において、人間の尊厳と個人の自律を尊重し、\n"
                "人間中心の原則に基づくAI活用を推進することを目的とする。\n\n"
                "## 2. 基本原則\n"
                "- AIは人間の意思決定を支援するツールであり、最終判断は人間が行う\n"
                "- AIの利用は人間の尊厳を損なわない範囲で行う\n"
                "- AIの判断に対して、人間が異議を申し立てる権利を保障する\n\n"
                "## 3. 適用範囲\n"
                "本方針は、{org_name}の全部門・全従業員に適用される。\n\n"
                "## 4. 周知・教育\n"
                "本方針は全従業員に周知し、定期的な研修を通じて理解を深める。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。組織の実態に合わせて修正してください。*"
            ),
        ),
        DocumentDefinition(
            title="従業員周知用1ページサマリー",
            doc_type="template",
            template=(
                "# AI利用基本方針 サマリー\n\n"
                "**{org_name}のAI利用3つの約束**\n\n"
                "1. **人間が主役**: AIの判断は参考情報です。最終判断は必ず人間が行います。\n"
                "2. **尊厳の尊重**: AIは人権を侵害する目的では使用しません。\n"
                "3. **異議申立ての権利**: AIの判断に疑問がある場合、いつでも異議を申し立てられます。\n\n"
                "**困ったときは**: AIガバナンス担当者にご相談ください。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
        DocumentDefinition(
            title="研修実施チェックリスト",
            doc_type="checklist",
            template=(
                "# AI利用方針 研修実施チェックリスト\n\n"
                "**組織名**: {org_name}\n\n"
                "- [ ] 研修資料を作成した\n"
                "- [ ] 研修日程を決定し、全従業員に通知した\n"
                "- [ ] 研修を実施した\n"
                "- [ ] 受講者名簿を記録した\n"
                "- [ ] 理解度テストまたはアンケートを実施した\n"
                "- [ ] 未受講者へのフォローアップを計画した\n"
                "- [ ] 研修記録をエビデンスとして保管した\n"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI利用基本方針を策定する",
            description="人間中心の原則を明記したAI利用基本方針を策定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="経営層の承認を得る",
            description="策定した方針について経営層の承認を取得する",
            assignee_role="AIガバナンス責任者",
            deadline_days=21,
            depends_on=[0],
        ),
        TaskDefinition(
            title="全社周知を行う",
            description="承認された方針を全従業員に周知する",
            assignee_role="人事・総務部門",
            deadline_days=30,
            depends_on=[1],
        ),
        TaskDefinition(
            title="研修を実施する",
            description="全従業員を対象としたAI利用方針の研修を実施する",
            assignee_role="人事・総務部門",
            deadline_days=60,
            depends_on=[2],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI利用基本方針は文書として策定されていますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="方針は経営層の承認を得ていますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="全従業員に周知されていますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="研修を実施し、受講記録を保管していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C01-R02: 意思決定における人間の関与 ─────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C01-R02",
    documents=[
        DocumentDefinition(
            title="Human-in-the-Loop運用手順書",
            doc_type="procedure",
            template=(
                "# Human-in-the-Loop 運用手順書\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 目的\n"
                "AIシステムの判断に対し、人間が最終確認・承認を行うプロセスを定める。\n\n"
                "## 2. 対象システム\n"
                "高リスクAIシステム（意思決定支援、審査・評価、自動判定等）\n\n"
                "## 3. 人間関与のレベル\n"
                "| レベル | 内容 | 対象 |\n"
                "|--------|------|------|\n"
                "| Human-in-the-Loop | 人間が毎回判断を確認・承認 | 高リスク判定 |\n"
                "| Human-on-the-Loop | 人間が定期的に監視・介入 | 中リスク業務 |\n"
                "| Human-in-Command | 人間がいつでも停止・変更可能 | 全AIシステム |\n\n"
                "## 4. 運用ルール\n"
                "- 高リスク判定はAI判断後に必ず人間が確認する\n"
                "- 承認者は判断根拠を確認し、記録を残す\n"
                "- 異常を検知した場合は即座にシステムを停止できる\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="高リスクAIシステムを特定する",
            description="組織内のAIシステムのうち、高リスク判定が必要なものを洗い出す",
            assignee_role="AIガバナンス責任者",
            deadline_days=7,
        ),
        TaskDefinition(
            title="Human-in-the-Loop承認プロセスを設計する",
            description="各高リスクシステムに対する人間の確認・承認フローを設計する",
            assignee_role="システム管理者",
            deadline_days=21,
            depends_on=[0],
        ),
        TaskDefinition(
            title="承認プロセスを実装・導入する",
            description="設計した承認プロセスをシステムに組み込む",
            assignee_role="開発チーム",
            deadline_days=45,
            depends_on=[1],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="高リスクAIシステムの判断に人間の承認プロセスがありますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="承認記録を保管していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C01-R03: 誤情報・偽情報への対処 ─────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C01-R03",
    documents=[
        DocumentDefinition(
            title="AI出力検証ガイドライン",
            doc_type="procedure",
            template=(
                "# AI出力検証ガイドライン\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 目的\n"
                "AI生成コンテンツの正確性を確認し、誤情報・偽情報の拡散を防止する。\n\n"
                "## 2. 検証プロセス\n"
                "1. AI出力を受け取ったら、事実関係を信頼できる情報源で確認する\n"
                "2. 数値データは元データと照合する\n"
                "3. 重要な意思決定に使う情報は、複数の情報源で裏付けを取る\n\n"
                "## 3. 禁止事項\n"
                "- AI出力を検証なしに外部公開すること\n"
                "- AI出力を事実として引用すること（検証なし）\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI出力のファクトチェックプロセスを整備する",
            description="AI生成コンテンツの正確性を確認するプロセスを策定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="誤情報検出の仕組みを導入する",
            description="AI出力の誤り検出・フィルタリングの仕組みを検討・導入する",
            assignee_role="開発チーム",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI出力の検証プロセスが文書化されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C02-R01: リスクアセスメントの実施 ───────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C02-R01",
    documents=[
        DocumentDefinition(
            title="AIリスクアセスメントシート",
            doc_type="template",
            template=(
                "# AIリスクアセスメントシート\n\n"
                "**組織名**: {org_name}\n"
                "**評価日**: {date}\n"
                "**評価者**: _______________\n\n"
                "## 対象AIシステム\n"
                "| 項目 | 内容 |\n"
                "|------|------|\n"
                "| システム名 | |\n"
                "| 用途 | |\n"
                "| 利用部門 | |\n"
                "| 利用開始日 | |\n\n"
                "## リスク評価\n"
                "| リスク項目 | 影響度(1-5) | 発生確率(1-5) | リスク値 | 対策 |\n"
                "|-----------|------------|-------------|---------|------|\n"
                "| バイアス・差別 | | | | |\n"
                "| 個人情報漏洩 | | | | |\n"
                "| 誤判定・誤出力 | | | | |\n"
                "| セキュリティ攻撃 | | | | |\n"
                "| システム障害 | | | | |\n"
                "| 法令違反 | | | | |\n"
                "| 倫理的問題 | | | | |\n\n"
                "## リスクマトリクス\n"
                "```\n"
                "影響度 5 | 中 | 高 | 高 | 極高 | 極高\n"
                "       4 | 中 | 中 | 高 | 高  | 極高\n"
                "       3 | 低 | 中 | 中 | 高  | 高\n"
                "       2 | 低 | 低 | 中 | 中  | 高\n"
                "       1 | 低 | 低 | 低 | 中  | 中\n"
                "         --------------------------\n"
                "           1    2    3    4     5  発生確率\n"
                "```\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
        DocumentDefinition(
            title="リスク台帳テンプレート",
            doc_type="template",
            template=(
                "# AIリスク台帳\n\n"
                "**組織名**: {org_name}\n"
                "**最終更新日**: {date}\n\n"
                "| No | リスクID | AIシステム | リスク内容 | 影響度 | 発生確率 | リスク値 | 対策状況 | 担当者 | 期限 |\n"
                "|----|---------|-----------|----------|--------|---------|---------|---------|--------|------|\n"
                "| 1 | R-001 | | | | | | 未着手 | | |\n"
                "| 2 | R-002 | | | | | | 未着手 | | |\n"
                "| 3 | R-003 | | | | | | 未着手 | | |\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AIシステム台帳から対象システムを特定する",
            description="リスクアセスメントの対象となるAIシステムを洗い出す",
            assignee_role="AIガバナンス責任者",
            deadline_days=7,
        ),
        TaskDefinition(
            title="リスク評価を実施する",
            description="各AIシステムについてリスクアセスメントシートに基づき評価を実施する",
            assignee_role="リスク管理担当者",
            deadline_days=21,
            depends_on=[0],
        ),
        TaskDefinition(
            title="リスク台帳に結果を記録する",
            description="評価結果をリスク台帳に記録し、対策計画を立てる",
            assignee_role="リスク管理担当者",
            deadline_days=28,
            depends_on=[1],
        ),
        TaskDefinition(
            title="対策を計画・実行する",
            description="高リスク項目から優先的に対策を計画し実行する",
            assignee_role="各対策担当者",
            deadline_days=60,
            depends_on=[2],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="全AIシステムのリスクアセスメントを実施しましたか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="リスク台帳を作成・更新していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="高リスク項目に対する対策を実施していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C02-R02: 学習データの品質管理 ───────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C02-R02",
    documents=[
        DocumentDefinition(
            title="学習データ品質管理基準",
            doc_type="policy",
            template=(
                "# 学習データ品質管理基準\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 品質基準\n"
                "- 正確性: データの誤り率が1%未満であること\n"
                "- 網羅性: 対象ドメインを十分にカバーしていること\n"
                "- 偏り: 特定属性への過度な偏りがないこと\n"
                "- 鮮度: データが最新の状況を反映していること\n\n"
                "## 2. 品質チェックプロセス\n"
                "1. データ収集時の品質チェック\n"
                "2. 前処理後の品質検証\n"
                "3. 定期的な品質監査（四半期ごと）\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="学習データの品質基準を定義する",
            description="データの正確性・網羅性・偏りに関する品質基準を策定する",
            assignee_role="データ管理責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="品質監査プロセスを導入する",
            description="データ品質の定期監査プロセスを設計・導入する",
            assignee_role="データ管理責任者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="学習データの品質基準を文書化していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="定期的な品質監査を実施していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C02-R03: 安全な運用・停止手順 ───────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C02-R03",
    documents=[
        DocumentDefinition(
            title="AIシステム安全停止手順書",
            doc_type="procedure",
            template=(
                "# AIシステム安全停止手順書\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 目的\n"
                "AIシステムに異常が発生した場合の安全な停止手順とフォールバック手段を定める。\n\n"
                "## 2. 異常検知基準\n"
                "- 出力精度が閾値を下回った場合\n"
                "- 応答時間が規定値を超えた場合\n"
                "- セキュリティアラートが発生した場合\n\n"
                "## 3. 停止手順\n"
                "1. 異常を検知・報告する\n"
                "2. 影響範囲を特定する\n"
                "3. AIシステムを安全に停止する\n"
                "4. フォールバック手段に切り替える\n"
                "5. 原因を調査・是正する\n"
                "6. 安全確認後にシステムを再開する\n\n"
                "## 4. フォールバック手段\n"
                "| AIシステム | フォールバック手段 | 切替手順 |\n"
                "|-----------|------------------|----------|\n"
                "| [システム名] | [手動処理等] | [手順] |\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="安全停止手順書を作成する",
            description="AIシステムの異常時の安全停止手順とフォールバック手段を文書化する",
            assignee_role="システム管理者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="フォールバック手段を設計・実装する",
            description="各AIシステムのフォールバック手段を設計し実装する",
            assignee_role="開発チーム",
            deadline_days=30,
            depends_on=[0],
        ),
        TaskDefinition(
            title="停止手順の訓練を実施する",
            description="定期的な停止手順の訓練を実施する",
            assignee_role="システム管理者",
            deadline_days=45,
            depends_on=[1],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="安全停止手順書が作成されていますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="フォールバック手段が用意されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C03-R01: バイアス評価の実施 ─────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C03-R01",
    documents=[
        DocumentDefinition(
            title="バイアス評価チェックリスト",
            doc_type="checklist",
            template=(
                "# バイアス評価チェックリスト\n\n"
                "**組織名**: {org_name}\n"
                "**評価日**: {date}\n\n"
                "## データバイアス\n"
                "- [ ] 学習データの属性分布を確認した\n"
                "- [ ] 特定グループの過剰/過少代表がないか確認した\n"
                "- [ ] 歴史的バイアスの有無を検討した\n\n"
                "## モデルバイアス\n"
                "- [ ] 保護属性ごとの精度差を測定した\n"
                "- [ ] 公平性指標（DPR, EOR等）を計算した\n"
                "- [ ] 閾値を超えるバイアスがないか確認した\n\n"
                "## 運用バイアス\n"
                "- [ ] 実運用データでのバイアスモニタリングを設定した\n"
                "- [ ] 定期的な再評価スケジュールを策定した\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="バイアス評価の定量的指標を定義する",
            description="公平性の測定指標と閾値を決定する",
            assignee_role="データサイエンティスト",
            deadline_days=14,
        ),
        TaskDefinition(
            title="バイアスオーディットを実施する",
            description="全AIシステムについてバイアス評価を実施する",
            assignee_role="データサイエンティスト",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="バイアス評価の指標と閾値を定義していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="定期的なバイアス評価を実施していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C03-R02: 公平性基準の策定 ───────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C03-R02",
    documents=[
        DocumentDefinition(
            title="AI公平性基準書",
            doc_type="policy",
            template=(
                "# AI公平性基準書\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 公平性の定義\n"
                "利用文脈に応じた公平性基準を以下のように定義する。\n\n"
                "## 2. 保護属性\n"
                "性別、年齢、人種、国籍、障害の有無、宗教、社会的身分\n\n"
                "## 3. モニタリング\n"
                "四半期ごとに公平性指標を測定し、基準を満たしていることを確認する。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="利用文脈に応じた公平性基準を策定する",
            description="各AIシステムの利用文脈に適した公平性基準を策定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="公平性モニタリングダッシュボードを構築する",
            description="公平性指標を継続的に監視するダッシュボードを構築する",
            assignee_role="開発チーム",
            deadline_days=45,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="利用文脈に応じた公平性基準を策定していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C03-R03: 差別的影響の是正措置 ───────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C03-R03",
    documents=[
        DocumentDefinition(
            title="バイアス是正手順書",
            doc_type="procedure",
            template=(
                "# バイアス是正手順書\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 検出時の初動\n"
                "1. バイアス検出報告を受理する\n"
                "2. 影響範囲を特定する\n"
                "3. 是正の緊急度を判定する\n\n"
                "## 2. 是正手順\n"
                "1. 原因分析（データ/モデル/運用）\n"
                "2. 是正措置の選択と実施\n"
                "3. 是正後の効果検証\n\n"
                "## 3. 責任者\n"
                "是正措置の実施責任者: [担当者名]\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="バイアス是正手順と責任者を明確にする",
            description="バイアス検出時の是正手順を策定し、責任者を指定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="是正後の効果検証プロセスを整備する",
            description="是正措置の効果を検証するプロセスを整備する",
            assignee_role="データサイエンティスト",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="バイアス検出時の是正手順が文書化されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C04-R01: 個人情報取扱方針の策定 ─────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C04-R01",
    documents=[
        DocumentDefinition(
            title="AI固有プライバシーポリシー",
            doc_type="policy",
            template=(
                "# AIシステムにおける個人情報取扱方針\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 目的\n"
                "AIシステムにおける個人情報の取得・利用・提供・保管・削除に関する方針を定める。\n\n"
                "## 2. 個人情報の取扱い\n"
                "### 2.1 取得\n"
                "- 利用目的を明示し、必要最小限のデータのみ取得する\n"
                "- 本人の同意を得て取得する\n\n"
                "### 2.2 利用\n"
                "- 明示した目的の範囲内でのみ利用する\n"
                "- AI学習への利用は別途同意を取得する\n\n"
                "### 2.3 保管・削除\n"
                "- 保管期間を定め、期間経過後は安全に削除する\n"
                "- 適切なセキュリティ措置を講じて保管する\n\n"
                "## 3. 公表・開示\n"
                "本方針はWebサイト等で公表する。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="既存プライバシーポリシーを確認する",
            description="現在のプライバシーポリシーの内容を確認し、AI固有の不足点を洗い出す",
            assignee_role="法務担当者",
            deadline_days=7,
        ),
        TaskDefinition(
            title="AI固有セクションを追加する",
            description="プライバシーポリシーにAI固有の個人情報取扱いセクションを追加する",
            assignee_role="法務担当者",
            deadline_days=21,
            depends_on=[0],
        ),
        TaskDefinition(
            title="法務レビューを実施する",
            description="更新したポリシーの法務レビューを実施する",
            assignee_role="法務担当者",
            deadline_days=30,
            depends_on=[1],
        ),
        TaskDefinition(
            title="ポリシーを公開する",
            description="レビュー完了後、ポリシーを公開する",
            assignee_role="広報・Web担当",
            deadline_days=35,
            depends_on=[2],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI固有の個人情報取扱方針を策定していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="ポリシーは一般に公表されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C04-R02: プライバシー影響評価 ───────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C04-R02",
    documents=[
        DocumentDefinition(
            title="プライバシー影響評価（PIA）テンプレート",
            doc_type="template",
            template=(
                "# プライバシー影響評価（PIA）\n\n"
                "**組織名**: {org_name}\n"
                "**評価日**: {date}\n"
                "**対象システム**: _______________\n\n"
                "## 1. システム概要\n"
                "| 項目 | 内容 |\n"
                "|------|------|\n"
                "| システム名 | |\n"
                "| 利用目的 | |\n"
                "| 処理する個人情報の種類 | |\n"
                "| データ量（概算） | |\n\n"
                "## 2. プライバシーリスク評価\n"
                "| リスク | 影響度(1-5) | 発生確率(1-5) | 対策 |\n"
                "|--------|-----------|-------------|------|\n"
                "| 意図しないデータ漏洩 | | | |\n"
                "| 目的外利用 | | | |\n"
                "| 過剰なデータ収集 | | | |\n"
                "| 同意なき利用 | | | |\n"
                "| プロファイリング | | | |\n\n"
                "## 3. 判定\n"
                "- [ ] リスクは許容範囲内\n"
                "- [ ] 追加対策が必要\n"
                "- [ ] 導入を見送る\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="PIA対象のAIシステムを特定する",
            description="プライバシー影響評価の対象となるAIシステムを洗い出す",
            assignee_role="プライバシー管理者",
            deadline_days=7,
        ),
        TaskDefinition(
            title="PIAを実施する",
            description="各対象システムについてPIAを実施する",
            assignee_role="プライバシー管理者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIシステム導入前にPIAを実施していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C04-R03: データ最小化・目的外利用禁止 ───────────────────────────

_register(AutoFixDefinition(
    requirement_id="C04-R03",
    documents=[
        DocumentDefinition(
            title="データ最小化チェックリスト",
            doc_type="checklist",
            template=(
                "# データ最小化チェックリスト\n\n"
                "**組織名**: {org_name}\n\n"
                "- [ ] 収集するデータ項目は目的に対して必要最小限か\n"
                "- [ ] データの利用目的は明確に定義されているか\n"
                "- [ ] 目的外利用を防止する技術的措置があるか\n"
                "- [ ] データ保持期間は定められているか\n"
                "- [ ] 不要になったデータの削除手順があるか\n"
                "- [ ] アクセス権限は最小限に設定されているか\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="データ最小化の原則をAI設計に組み込む",
            description="AIシステムの設計段階でデータ最小化の原則を適用する",
            assignee_role="開発チーム",
            deadline_days=21,
        ),
        TaskDefinition(
            title="目的外利用防止措置を講じる",
            description="技術的・組織的な目的外利用防止措置を実装する",
            assignee_role="セキュリティ担当者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="データ最小化の原則を適用していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C05-R01: セキュリティ対策の実施 ─────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C05-R01",
    documents=[
        DocumentDefinition(
            title="AI脅威モデリングシート",
            doc_type="template",
            template=(
                "# AI脅威モデリングシート\n\n"
                "**組織名**: {org_name}\n"
                "**評価日**: {date}\n\n"
                "## 対象システム: _______________\n\n"
                "## 脅威一覧\n"
                "| 脅威カテゴリ | 具体的な脅威 | 影響度 | 対策状況 |\n"
                "|------------|------------|--------|--------|\n"
                "| 敵対的攻撃 | 敵対的サンプル（Adversarial Examples） | | |\n"
                "| データポイズニング | 学習データの汚染 | | |\n"
                "| プロンプトインジェクション | 入力操作による不正出力 | | |\n"
                "| モデル抽出 | モデルの不正コピー | | |\n"
                "| メンバーシップ推論 | 学習データの推測 | | |\n"
                "| バックドア攻撃 | 隠し機能の埋め込み | | |\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
        DocumentDefinition(
            title="AIセキュリティチェックリスト",
            doc_type="checklist",
            template=(
                "# AIセキュリティチェックリスト\n\n"
                "**組織名**: {org_name}\n\n"
                "## 敵対的攻撃対策\n"
                "- [ ] 入力バリデーションを実装している\n"
                "- [ ] 敵対的学習（Adversarial Training）を検討した\n"
                "- [ ] 異常入力の検出機能がある\n\n"
                "## データ保護\n"
                "- [ ] 学習データのアクセス制御を実施している\n"
                "- [ ] データの整合性チェックを行っている\n"
                "- [ ] データの暗号化を実施している\n\n"
                "## プロンプトインジェクション対策\n"
                "- [ ] 入力のサニタイズ処理を実装している\n"
                "- [ ] システムプロンプトの保護措置がある\n"
                "- [ ] 出力フィルタリングを実装している\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI脅威分析を実施する",
            description="各AIシステムに対する脅威を分析し、脅威モデリングシートを作成する",
            assignee_role="セキュリティ担当者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="セキュリティ対策を実装する",
            description="脅威分析に基づくセキュリティ対策を実装する",
            assignee_role="開発チーム",
            deadline_days=45,
            depends_on=[0],
        ),
        TaskDefinition(
            title="ペネトレーションテストを実施する",
            description="AI固有の攻撃手法を含むペネトレーションテストを実施する",
            assignee_role="セキュリティ担当者",
            deadline_days=60,
            depends_on=[1],
        ),
        TaskDefinition(
            title="テスト結果を記録する",
            description="ペネトレーションテストの結果をエビデンスとして記録する",
            assignee_role="セキュリティ担当者",
            deadline_days=65,
            depends_on=[2],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI固有の脅威分析を実施していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="敵対的攻撃への防御策を講じていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C05-R02: 脆弱性管理 ─────────────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C05-R02",
    documents=[
        DocumentDefinition(
            title="AI脆弱性管理手順書",
            doc_type="procedure",
            template=(
                "# AI脆弱性管理手順書\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 脆弱性スキャン\n"
                "- 四半期ごとにAIシステムの脆弱性スキャンを実施する\n"
                "- 新たな脆弱性情報を継続的にモニタリングする\n\n"
                "## 2. 脆弱性対応\n"
                "1. 脆弱性を評価（CVSS等）\n"
                "2. 対応優先度を決定\n"
                "3. パッチ適用・設定変更\n"
                "4. 対応結果を記録\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="脆弱性管理プロセスを確立する",
            description="AIシステムの脆弱性管理プロセスを策定する",
            assignee_role="セキュリティ担当者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="脆弱性スキャンを実施する",
            description="脆弱性スキャンの自動化と修正追跡を行う",
            assignee_role="セキュリティ担当者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="定期的な脆弱性スキャンを実施していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C05-R03: インシデント対応体制 ───────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C05-R03",
    documents=[
        DocumentDefinition(
            title="AIセキュリティインシデント対応計画",
            doc_type="procedure",
            template=(
                "# AIセキュリティインシデント対応計画\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 対応体制\n"
                "| 役割 | 担当 | 連絡先 |\n"
                "|------|------|--------|\n"
                "| インシデント責任者 | | |\n"
                "| 技術対応チーム | | |\n"
                "| 広報担当 | | |\n"
                "| 法務担当 | | |\n\n"
                "## 2. 対応フロー\n"
                "検知 → 報告 → 初動対応 → 影響調査 → 是正 → 報告 → 記録\n\n"
                "## 3. 訓練\n"
                "年1回以上のインシデント対応訓練を実施する\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="インシデント対応計画を策定する",
            description="AIセキュリティインシデント対応計画を策定する",
            assignee_role="セキュリティ担当者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="対応手順の訓練を実施する",
            description="定期的なインシデント対応訓練を実施する",
            assignee_role="セキュリティ担当者",
            deadline_days=45,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIインシデント対応計画が策定されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C06-R01: AI利用の明示 ───────────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C06-R01",
    documents=[
        DocumentDefinition(
            title="AI利用開示ポリシー",
            doc_type="policy",
            template=(
                "# AI利用開示ポリシー\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 開示方針\n"
                "当社がAIを利用していることを、利害関係者に適切に開示する。\n\n"
                "## 2. 開示方法\n"
                "- サービス画面でのAI利用表示\n"
                "- 利用規約への記載\n"
                "- AI生成コンテンツへのラベル付け\n\n"
                "## 3. 対象\n"
                "顧客、従業員、取引先等すべての利害関係者\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI利用の開示ポリシーを策定する",
            description="AIの利用を利害関係者に明示するポリシーを策定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="サービス画面でのAI利用表示を実装する",
            description="AI利用表示をサービス画面やドキュメントに実装する",
            assignee_role="開発チーム",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI利用を利害関係者に開示していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C06-R02: 判断根拠の説明 ─────────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C06-R02",
    documents=[
        DocumentDefinition(
            title="AI判断説明テンプレート",
            doc_type="template",
            template=(
                "# AI判断根拠説明テンプレート\n\n"
                "**組織名**: {org_name}\n\n"
                "## 利用者向け説明フォーマット\n\n"
                "### AIの判断結果\n"
                "[判断内容を記載]\n\n"
                "### 判断の主な根拠\n"
                "1. [根拠1]\n"
                "2. [根拠2]\n"
                "3. [根拠3]\n\n"
                "### 注意事項\n"
                "- この判断はAIによるものであり、最終判断は人間が行います\n"
                "- ご不明点やご意見がある場合は、[窓口]までお問い合わせください\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI判断の説明生成機能を設計する",
            description="AI判断の説明生成機能を設計・実装する",
            assignee_role="開発チーム",
            deadline_days=30,
        ),
        TaskDefinition(
            title="利用者向け説明テンプレートを作成する",
            description="利用者向けの判断根拠説明テンプレートを作成する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIの判断根拠を説明する仕組みがありますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C06-R03: 技術情報の文書化 ───────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C06-R03",
    documents=[
        DocumentDefinition(
            title="モデルカードテンプレート",
            doc_type="template",
            template=(
                "# モデルカード\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## モデル概要\n"
                "| 項目 | 内容 |\n"
                "|------|------|\n"
                "| モデル名 | |\n"
                "| バージョン | |\n"
                "| 用途 | |\n"
                "| 開発者 | |\n"
                "| 利用開始日 | |\n\n"
                "## 学習データ\n"
                "| 項目 | 内容 |\n"
                "|------|------|\n"
                "| データソース | |\n"
                "| データ量 | |\n"
                "| 前処理方法 | |\n\n"
                "## 性能指標\n"
                "| 指標 | 値 |\n"
                "|------|----|\n"
                "| 精度 | |\n"
                "| 適合率 | |\n"
                "| 再現率 | |\n\n"
                "## 制限事項\n"
                "[既知の制限事項を記載]\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="モデルカードを作成する",
            description="各AIモデルのモデルカードを標準フォーマットで作成する",
            assignee_role="開発チーム",
            deadline_days=21,
        ),
        TaskDefinition(
            title="バージョン管理体制を構築する",
            description="技術文書のバージョン管理と変更履歴の体制を構築する",
            assignee_role="開発チーム",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIシステムの技術文書（モデルカード等）を整備していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C07-R01: 責任者の指定 ───────────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C07-R01",
    documents=[
        DocumentDefinition(
            title="AIガバナンス責任者任命書",
            doc_type="template",
            template=(
                "# AIガバナンス責任者任命書\n\n"
                "**組織名**: {org_name}\n"
                "**任命日**: {date}\n\n"
                "## 任命\n"
                "以下の者をAIガバナンス責任者に任命する。\n\n"
                "- **氏名**: _______________\n"
                "- **役職**: _______________\n\n"
                "## 権限と責任\n"
                "1. AIガバナンスに関する方針の策定・改定の承認\n"
                "2. AIシステムの導入・変更に関する最終判断\n"
                "3. インシデント発生時の対応指揮\n"
                "4. 定期的なガバナンス状況の経営層への報告\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AIガバナンス責任者を正式に任命する",
            description="AIガバナンスに関する責任者を正式に任命し、任命書を発行する",
            assignee_role="経営層",
            deadline_days=7,
        ),
        TaskDefinition(
            title="責任者の権限・責任を組織内文書で明確にする",
            description="責任者の権限と責任範囲を組織内で明文化し周知する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIガバナンス責任者が正式に任命されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C07-R02: ガバナンス方針・体制の整備 ─────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C07-R02",
    documents=[
        DocumentDefinition(
            title="AIガバナンス方針",
            doc_type="policy",
            template=(
                "# AIガバナンス方針\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 目的\n"
                "AIの開発・提供・利用に関するガバナンス方針を定め、実施体制を整備する。\n\n"
                "## 2. ガバナンス体制\n"
                "- AIガバナンス責任者: [役職名]\n"
                "- AIガバナンス委員会: [構成を記載]\n"
                "- 各部門AI責任者: [各部門から選出]\n\n"
                "## 3. PDCAサイクル\n"
                "- Plan: 方針策定・計画\n"
                "- Do: 実施・運用\n"
                "- Check: 監査・評価\n"
                "- Act: 改善・見直し\n\n"
                "## 4. レビュー\n"
                "本方針は年1回以上見直しを行う。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AIガバナンス方針を策定する",
            description="AIの開発・提供・利用に関するガバナンス方針を策定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=21,
        ),
        TaskDefinition(
            title="実施体制を整備する",
            description="ガバナンス方針に基づく実施体制を整備する",
            assignee_role="AIガバナンス責任者",
            deadline_days=30,
            depends_on=[0],
        ),
        TaskDefinition(
            title="定期レビューサイクルを確立する",
            description="定期的な方針レビューと改善サイクルを確立する",
            assignee_role="AIガバナンス責任者",
            deadline_days=45,
            depends_on=[1],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIガバナンス方針が策定されていますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="ガバナンスの実施体制が整備されていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C07-R03: 契約・SLAの整備 ───────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C07-R03",
    documents=[
        DocumentDefinition(
            title="AI関連契約チェックリスト",
            doc_type="checklist",
            template=(
                "# AI関連契約チェックリスト\n\n"
                "**組織名**: {org_name}\n\n"
                "## 契約に含めるべき条項\n"
                "- [ ] 責任分界（AIの判断に起因する損害の責任分担）\n"
                "- [ ] 品質保証（精度、応答時間、可用性のSLA）\n"
                "- [ ] データ取扱条件（所有権、利用範囲、削除義務）\n"
                "- [ ] セキュリティ要件\n"
                "- [ ] 監査権限\n"
                "- [ ] 免責条項\n"
                "- [ ] 解約条件（データ返却・削除）\n"
                "- [ ] 変更管理（モデル変更の事前通知）\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI関連契約の標準テンプレートを作成する",
            description="AI関連の取引に使用する標準契約テンプレートを作成する",
            assignee_role="法務担当者",
            deadline_days=21,
        ),
        TaskDefinition(
            title="責任分界・品質保証条項を明確にする",
            description="契約における責任分界とSLAを明確に定義する",
            assignee_role="法務担当者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI関連契約に必要な条項が含まれていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C07-R04: ガバナンス記録の保持 ───────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C07-R04",
    documents=[
        DocumentDefinition(
            title="ガバナンス記録管理規程",
            doc_type="policy",
            template=(
                "# ガバナンス記録管理規程\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 記録対象\n"
                "- 方針・手順の策定・改定記録\n"
                "- 意思決定記録\n"
                "- リスク評価記録\n"
                "- インシデント対応記録\n"
                "- 監査記録\n\n"
                "## 2. 管理方法\n"
                "- 統一的な記録管理システムで管理する\n"
                "- 改竄防止措置を講じる\n"
                "- 検索可能な状態を維持する\n\n"
                "## 3. 保存期間\n"
                "最低5年間保存する\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="ガバナンス記録の統一管理システムを導入する",
            description="ガバナンスに関する記録の統一管理システムを導入する",
            assignee_role="システム管理者",
            deadline_days=30,
        ),
        TaskDefinition(
            title="改竄防止付き監査証跡を実装する",
            description="改竄防止機能付きの監査証跡を実装する",
            assignee_role="開発チーム",
            deadline_days=45,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="ガバナンス記録を統一的に管理していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="改竄防止措置を講じていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C08-R01: 従業員教育の実施 ───────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C08-R01",
    documents=[
        DocumentDefinition(
            title="AI教育プログラム設計書",
            doc_type="template",
            template=(
                "# AI教育プログラム設計書\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 教育対象と内容\n"
                "| 対象 | 内容 | 頻度 | 時間 |\n"
                "|------|------|------|------|\n"
                "| 全従業員 | AI基礎・利用ルール | 年1回 | 2時間 |\n"
                "| AI利用部門 | AI活用スキル・リスク管理 | 半年1回 | 4時間 |\n"
                "| 開発者 | AIセキュリティ・倫理 | 四半期 | 4時間 |\n"
                "| 経営層 | AIガバナンス・戦略 | 年1回 | 2時間 |\n\n"
                "## 効果測定\n"
                "- 受講後テスト（正答率80%以上で合格）\n"
                "- 受講者アンケート\n"
                "- 業務適用状況の確認\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="役割別AI教育プログラムを設計する",
            description="全従業員・AI部門・開発者・経営層向けの教育プログラムを設計する",
            assignee_role="人事・総務部門",
            deadline_days=21,
        ),
        TaskDefinition(
            title="教育を実施する",
            description="設計した教育プログラムに基づき研修を実施する",
            assignee_role="人事・総務部門",
            deadline_days=60,
            depends_on=[0],
        ),
        TaskDefinition(
            title="教育効果の測定と改善サイクルを確立する",
            description="受講後テスト・アンケートによる効果測定と改善サイクルを確立する",
            assignee_role="人事・総務部門",
            deadline_days=75,
            depends_on=[1],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI関連の従業員教育を定期的に実施していますか？",
            expected_answer="yes",
        ),
        SelfCheckQuestion(
            question="教育効果の測定を行っていますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C08-R02: 利用者への情報提供 ─────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C08-R02",
    documents=[
        DocumentDefinition(
            title="AIシステム利用者ガイドライン",
            doc_type="procedure",
            template=(
                "# AIシステム利用者ガイドライン\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. AIの正しい使い方\n"
                "- AIの出力は参考情報として扱い、最終判断は人間が行ってください\n"
                "- 機密情報・個人情報をAIに入力しないでください\n"
                "- 不審な出力を発見した場合は管理者に報告してください\n\n"
                "## 2. よくある質問（FAQ）\n"
                "Q: AIの判断は常に正しいですか？\n"
                "A: いいえ。AIは間違える可能性があります。必ず確認してください。\n\n"
                "## 3. サポート\n"
                "お問い合わせ: [サポート窓口]\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="利用者ガイドラインを作成する",
            description="AIシステム利用者向けのガイドラインとFAQを作成する",
            assignee_role="AIガバナンス責任者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="サポート体制を整備する",
            description="AIに関する問い合わせ・サポート体制を整備する",
            assignee_role="カスタマーサポート",
            deadline_days=21,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="利用者向けのガイドラインを提供していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C09-R01: 公正競争への配慮 ───────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C09-R01",
    documents=[
        DocumentDefinition(
            title="AI公正競争方針",
            doc_type="policy",
            template=(
                "# AI公正競争方針\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 基本方針\n"
                "AIの利用において、不当な競争制限行為を行わない。\n\n"
                "## 2. 禁止事項\n"
                "- AIを用いた不当な価格操作\n"
                "- AIによる不当な取引制限\n"
                "- AIを用いた優越的地位の濫用\n\n"
                "## 3. レビュー体制\n"
                "法務部門による定期的なコンプライアンスレビューを実施する。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AI公正競争方針を策定する",
            description="AI利用における公正競争方針を策定する",
            assignee_role="法務担当者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="競争法コンプライアンスレビュー体制を構築する",
            description="定期的な競争法コンプライアンスのレビュー体制を構築する",
            assignee_role="法務担当者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI利用における公正競争方針を策定していますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C09-R02: 知的財産の尊重 ─────────────────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C09-R02",
    documents=[
        DocumentDefinition(
            title="AI知的財産権チェックリスト",
            doc_type="checklist",
            template=(
                "# AI知的財産権チェックリスト\n\n"
                "**組織名**: {org_name}\n\n"
                "## 学習データ\n"
                "- [ ] 学習データの利用許諾を確認した\n"
                "- [ ] 著作権のあるコンテンツの利用条件を確認した\n"
                "- [ ] オープンソースライセンスの条件を遵守している\n\n"
                "## AI出力\n"
                "- [ ] AI生成コンテンツの著作権帰属を確認した\n"
                "- [ ] 他者の著作物に類似した出力のチェック体制がある\n"
                "- [ ] AI出力を商用利用する際のライセンス条件を確認した\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="知的財産権チェックリストを作成する",
            description="AI学習・利用における知的財産権チェックリストを作成する",
            assignee_role="法務担当者",
            deadline_days=14,
        ),
        TaskDefinition(
            title="知的財産権侵害リスクの評価プロセスを導入する",
            description="AI関連の知的財産権侵害リスクの評価プロセスを導入する",
            assignee_role="法務担当者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AI利用における知的財産権のチェック体制がありますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C10-R01: イノベーション促進への貢献 ─────────────────────────────

_register(AutoFixDefinition(
    requirement_id="C10-R01",
    documents=[
        DocumentDefinition(
            title="AIイノベーション推進ロードマップ",
            doc_type="template",
            template=(
                "# AIイノベーション推進ロードマップ\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 短期目標（6ヶ月以内）\n"
                "- [ ] AI活用の現状評価\n"
                "- [ ] 重点領域の特定\n"
                "- [ ] パイロットプロジェクトの立ち上げ\n\n"
                "## 中期目標（1年以内）\n"
                "- [ ] 本格的なAI導入\n"
                "- [ ] 社外連携の開始\n\n"
                "## 長期目標（2年以内）\n"
                "- [ ] エコシステムへの参加・貢献\n"
                "- [ ] 社会課題解決への取り組み\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="AIイノベーション推進ロードマップを策定する",
            description="AIを通じたイノベーション推進のロードマップを策定する",
            assignee_role="AIガバナンス責任者",
            deadline_days=30,
        ),
        TaskDefinition(
            title="社外連携の機会を探索する",
            description="オープンイノベーション・産学連携の機会を探索する",
            assignee_role="事業開発担当",
            deadline_days=60,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="AIイノベーション推進のロードマップがありますか？",
            expected_answer="yes",
        ),
    ],
))

# ── C10-R02: 相互運用性・オープン性の確保 ───────────────────────────

_register(AutoFixDefinition(
    requirement_id="C10-R02",
    documents=[
        DocumentDefinition(
            title="相互運用性・オープン性方針",
            doc_type="policy",
            template=(
                "# 相互運用性・オープン性方針\n\n"
                "**組織名**: {org_name}\n"
                "**作成日**: {date}\n\n"
                "## 1. 基本方針\n"
                "技術的な囲い込みを避け、相互運用性とオープン性の確保に努める。\n\n"
                "## 2. 技術選定基準\n"
                "- オープンスタンダードへの準拠を優先する\n"
                "- ベンダーロックインを避けるアーキテクチャを採用する\n"
                "- データのポータビリティを確保する\n\n"
                "## 3. オープンソース貢献\n"
                "可能な範囲でオープンソースコミュニティへの貢献を推奨する。\n\n"
                "---\n"
                "*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
        ),
    ],
    tasks=[
        TaskDefinition(
            title="相互運用性を考慮したAI技術選定基準を策定する",
            description="オープンスタンダード準拠を含むAI技術選定基準を策定する",
            assignee_role="技術責任者",
            deadline_days=21,
        ),
        TaskDefinition(
            title="オープン標準への準拠方針を定める",
            description="組織としてのオープン標準への準拠方針を定める",
            assignee_role="技術責任者",
            deadline_days=30,
            depends_on=[0],
        ),
    ],
    self_check_questions=[
        SelfCheckQuestion(
            question="相互運用性を考慮した技術選定基準がありますか？",
            expected_answer="yes",
        ),
    ],
))


def get_autofix_definition(requirement_id: str) -> AutoFixDefinition | None:
    """要件IDからAutoFix定義を取得."""
    return AUTOFIX_DEFINITIONS.get(requirement_id)


def all_autofix_requirement_ids() -> list[str]:
    """AutoFix定義がある全要件IDのリスト."""
    return sorted(AUTOFIX_DEFINITIONS.keys())
