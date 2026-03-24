# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""ISO/IEC 42001:2023 (AIMS) 詳細要求事項・管理策・実装ガイダンス.

ISO/IEC 42001の各要求事項に対して以下を追加定義:
- 管理策 (Controls) の詳細リスト
- 実装ガイダンス
- エビデンス例（監査で求められる証拠の具体例）
- Common Gaps（企業がよく躓くポイント）
- チェック質問

参考:
- ISO/IEC 42001:2023 Information technology - Artificial intelligence - Management system
- ISO/IEC 42001 Annex A (normative) - Reference control objectives and controls
- ISO/IEC 42001 Annex B (informative) - Implementation guidance
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Control:
    """ISO 42001 管理策."""

    control_id: str  # e.g., "A.2.2"
    title: str
    description: str
    implementation_guidance: str = ""


@dataclass(frozen=True)
class DetailedRequirement:
    """ISO 42001 詳細要求事項."""

    req_id: str  # e.g., "ISO-4.1"
    clause: str
    title: str
    description: str
    controls: list[Control] = field(default_factory=list)
    implementation_guidance: list[str] = field(default_factory=list)
    evidence_examples: list[str] = field(default_factory=list)
    common_gaps: list[str] = field(default_factory=list)
    check_questions: list[str] = field(default_factory=list)
    meti_mapping: list[str] = field(default_factory=list)
    nist_mapping: list[str] = field(default_factory=list)
    eu_ai_act_mapping: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Annex A 管理策一覧
# ---------------------------------------------------------------------------

ANNEX_A_CONTROLS: list[Control] = [
    # ── A.2 AI方針 ──
    Control(
        control_id="A.2.2",
        title="AI方針",
        description="AIの開発及び利用に関する方針を確立し、トップマネジメントの承認を得て公表すること。",
        implementation_guidance=(
            "AI方針には以下を含めること: "
            "(a) AIの利用目的と期待される便益、"
            "(b) AIに関するリスク許容基準、"
            "(c) AI倫理原則、"
            "(d) ステークホルダーへのコミットメント。"
            "方針は定期的にレビューし、組織の状況変化に応じて更新する。"
        ),
    ),
    # ── A.3 内部組織 ──
    Control(
        control_id="A.3.2",
        title="AIに関する役割及び責任",
        description="AI関連の役割、責任、権限を定義し、割り当てること。",
        implementation_guidance=(
            "AIガバナンス委員会、AI倫理審査委員会、AIリスク管理責任者、"
            "AIシステムオーナー等の役割を明確に定義する。"
            "責任分担はRACIマトリクス等で文書化する。"
        ),
    ),
    Control(
        control_id="A.3.3",
        title="AIシステムへの関心のある利害関係者",
        description="AIシステムに関連する利害関係者を特定し、そのニーズと期待を把握すること。",
        implementation_guidance=(
            "利害関係者マッピングを実施し、内部（経営層、従業員、開発者）と"
            "外部（顧客、規制当局、社会）の利害関係者を網羅的に特定する。"
        ),
    ),
    # ── A.4 AIシステムのリソース ──
    Control(
        control_id="A.4.2",
        title="AIシステムに使用するデータ",
        description="AIシステムの学習・評価に使用するデータの品質を管理すること。",
        implementation_guidance=(
            "データの収集・前処理・ラベリング・品質評価のプロセスを確立する。"
            "データの出所（provenance）を記録し、バイアスの評価を行う。"
            "データの適切性を利用目的に照らして定期的にレビューする。"
        ),
    ),
    Control(
        control_id="A.4.3",
        title="AI開発・運用のための技術ツール",
        description="AI開発・運用に使用する技術ツール・インフラを適切に管理すること。",
        implementation_guidance=(
            "ML/AIフレームワーク、開発環境、本番環境、モニタリングツール等の"
            "選定基準・バージョン管理・セキュリティ設定を文書化する。"
        ),
    ),
    Control(
        control_id="A.4.4",
        title="AIシステムのインベントリ",
        description="組織内のAIシステムのインベントリ（台帳）を維持すること。",
        implementation_guidance=(
            "各AIシステムについて、名称、用途、リスクレベル、責任者、"
            "使用データ、利用開始日、ステータスを記録する。"
            "インベントリは最低年1回レビューする。"
        ),
    ),
    # ── A.5 AIシステムのライフサイクル ──
    Control(
        control_id="A.5.2",
        title="AI開発プロセス",
        description="AIシステムの開発プロセスを確立し、要件定義からデプロイまでのライフサイクルを管理すること。",
        implementation_guidance=(
            "以下のフェーズを含むプロセスを確立する: "
            "要件定義 → データ収集・準備 → モデル設計・学習 → 検証・テスト → "
            "デプロイ → モニタリング → 改善/退役。"
            "各フェーズのゲート条件を定義する。"
        ),
    ),
    Control(
        control_id="A.5.3",
        title="責任あるAIの実践",
        description="公平性、透明性、説明可能性等の責任あるAIの原則を実装すること。",
        implementation_guidance=(
            "バイアス検出・軽減の手法を組み込む。"
            "モデルの説明可能性（SHAP、LIME等）を考慮した設計を行う。"
            "AI出力に対する人間のレビュープロセスを設ける。"
        ),
    ),
    Control(
        control_id="A.5.4",
        title="AIシステムの文書化",
        description="AIシステムの技術仕様・設計判断・性能指標を文書化すること。",
        implementation_guidance=(
            "モデルカード、データシート、システム設計書を標準フォーマットで作成する。"
            "モデルの学習条件、ハイパーパラメータ、評価指標を記録する。"
        ),
    ),
    # ── A.6 AIシステムの影響評価 ──
    Control(
        control_id="A.6.2",
        title="AIシステム影響評価の実施",
        description="AIシステムが個人・社会に与える影響を体系的に評価すること。",
        implementation_guidance=(
            "影響評価では以下を対象とする: "
            "(a) 基本的人権への影響、"
            "(b) 安全性への影響、"
            "(c) 環境への影響、"
            "(d) 社会的影響（雇用、格差等）。"
            "高リスクと判定されたシステムには追加の軽減措置を講じる。"
        ),
    ),
    # ── A.7 AIシステムのサポート ──
    Control(
        control_id="A.7.2",
        title="AIの力量",
        description="AIに関わる人員の力量要件を定義し、必要な教育・訓練を提供すること。",
        implementation_guidance=(
            "役割別の力量要件マトリクスを作成する。"
            "AI開発者にはML/AI技術研修、管理者にはAIガバナンス研修、"
            "利用者にはAIリテラシー研修を提供する。"
        ),
    ),
    Control(
        control_id="A.7.3",
        title="利害関係者の認識",
        description="AIシステムの利害関係者がAIの特性・限界・リスクを認識していることを確認すること。",
        implementation_guidance=(
            "AI利用ガイドライン、FAQ、研修資料を提供し、"
            "利害関係者がAIシステムの能力と限界を理解していることを確認する。"
        ),
    ),
    # ── A.8 AIシステムの運用 ──
    Control(
        control_id="A.8.2",
        title="AIシステムのモニタリング",
        description="AIシステムのパフォーマンスを継続的にモニタリングすること。",
        implementation_guidance=(
            "モニタリング対象: 精度指標、データドリフト、概念ドリフト、"
            "応答時間、エラー率。閾値を設定し、アラートを構成する。"
            "モニタリング結果は定期的にレビューし、劣化時の対応手順を準備する。"
        ),
    ),
    Control(
        control_id="A.8.3",
        title="AIシステムのインシデント管理",
        description="AIシステムに関するインシデントの検出・報告・対応プロセスを確立すること。",
        implementation_guidance=(
            "インシデントの定義と分類基準を設定する。"
            "報告ルート、初動対応、根本原因分析、再発防止のプロセスを文書化する。"
            "重大インシデントの場合の外部報告（規制当局等）手順も含める。"
        ),
    ),
    # ── A.9 サードパーティ・サプライチェーン ──
    Control(
        control_id="A.9.2",
        title="サードパーティとの関係",
        description="AIに関するサードパーティ（ベンダー、データ提供者等）との関係を管理すること。",
        implementation_guidance=(
            "サードパーティのAI関連リスクを評価する。"
            "契約にAI品質基準、データ取扱条件、監査権限を含める。"
            "サプライチェーン上の責任分担を明確にする。"
        ),
    ),
    Control(
        control_id="A.9.3",
        title="AIシステムのサプライチェーン管理",
        description="AIサプライチェーン全体のリスクを管理すること。",
        implementation_guidance=(
            "学習済みモデル、事前学習データ、AI-as-a-Service等の"
            "サプライチェーンリスクを特定し、軽減策を講じる。"
        ),
    ),
    # ── A.10 AIシステムの開発・取得 ──
    Control(
        control_id="A.10.2",
        title="AIシステムのテスト",
        description="AIシステムの体系的なテスト戦略を策定・実施すること。",
        implementation_guidance=(
            "テスト戦略には以下を含める: "
            "単体テスト、統合テスト、システムテスト、受入テスト、"
            "ストレステスト、公平性テスト、セキュリティテスト、"
            "境界値テスト、adversarialテスト。"
        ),
    ),
]

_CONTROL_MAP: dict[str, Control] = {c.control_id: c for c in ANNEX_A_CONTROLS}


# ---------------------------------------------------------------------------
# 詳細要求事項
# ---------------------------------------------------------------------------

DETAILED_REQUIREMENTS: list[DetailedRequirement] = [
    # ── 4.1 組織とその状況の理解 ──
    DetailedRequirement(
        req_id="ISO-4.1",
        clause="4.1",
        title="組織とその状況の理解",
        description="AIマネジメントシステムの目的に関連する外部・内部の課題を決定すること。",
        controls=[
            _CONTROL_MAP["A.3.3"],
        ],
        implementation_guidance=[
            "PEST分析・SWOT分析を用いてAIに関連する外部・内部課題を特定する",
            "AI規制動向（EU AI Act、AI推進法等）を外部課題として考慮する",
            "組織のAI成熟度、技術力、文化を内部課題として評価する",
            "競合他社のAI活用状況を外部環境分析に含める",
        ],
        evidence_examples=[
            "外部・内部課題の分析レポート",
            "AI関連規制動向のモニタリング記録",
            "経営層によるレビュー議事録",
            "PEST/SWOT分析結果の文書",
        ],
        common_gaps=[
            "AI固有の課題ではなく一般的なIT課題のみを分析している",
            "規制動向のモニタリングが不定期",
            "組織のAI成熟度を客観的に評価していない",
            "利害関係者の期待変化を追跡していない",
        ],
        check_questions=[
            "AIに関連する外部環境（規制、市場、技術動向）を定期的に分析していますか？",
            "AIに関連する内部課題（技術力、組織文化、リソース）を把握していますか？",
            "分析結果はAIMSの計画に反映されていますか？",
        ],
        meti_mapping=["C07-R02"],
        nist_mapping=["GOVERN-1.1", "GOVERN-1.2"],
        eu_ai_act_mapping=["Art.9"],
    ),

    # ── 4.2 利害関係者のニーズ及び期待 ──
    DetailedRequirement(
        req_id="ISO-4.2",
        clause="4.2",
        title="利害関係者のニーズ及び期待の理解",
        description="AIマネジメントシステムに関連する利害関係者と、その要求事項を特定すること。",
        controls=[
            _CONTROL_MAP["A.3.3"],
        ],
        implementation_guidance=[
            "利害関係者マッピングを実施し、影響度と関心度で分類する",
            "各利害関係者のAIに関する期待・懸念を調査する",
            "法的要件（個人情報保護法、AI推進法等）を利害関係者要件に含める",
            "ステークホルダーエンゲージメント計画を策定する",
        ],
        evidence_examples=[
            "利害関係者一覧と要求事項マトリクス",
            "ステークホルダーアンケート・インタビュー結果",
            "法的要件一覧",
            "利害関係者エンゲージメント計画書",
        ],
        common_gaps=[
            "利害関係者の特定が不十分（AIの影響を受ける人々を見落とし）",
            "法的要件の網羅性が不足",
            "利害関係者の期待を定期的に更新していない",
        ],
        check_questions=[
            "AIシステムの影響を受ける全ての利害関係者を特定していますか？",
            "各利害関係者のAIに関する期待と懸念を把握していますか？",
            "利害関係者の要求事項は定期的にレビューされていますか？",
        ],
        meti_mapping=["C01-R01", "C06-R01"],
        nist_mapping=["GOVERN-1.1", "MAP-1.1"],
        eu_ai_act_mapping=["Art.9", "Art.13"],
    ),

    # ── 4.3 AIMSの適用範囲の決定 ──
    DetailedRequirement(
        req_id="ISO-4.3",
        clause="4.3",
        title="AIマネジメントシステムの適用範囲の決定",
        description="AIMSの適用範囲を決定し、文書化すること。",
        controls=[],
        implementation_guidance=[
            "適用範囲には対象AIシステム、部門、拠点、活動を明記する",
            "適用除外がある場合はその理由を文書化する",
            "適用範囲は組織の戦略的方向性と整合させる",
        ],
        evidence_examples=[
            "AIMS適用範囲記述書",
            "対象AIシステム一覧",
            "適用除外の理由書（該当する場合）",
        ],
        common_gaps=[
            "適用範囲が曖昧で、対象AIシステムが明確でない",
            "新しいAIシステムの追加時に適用範囲が更新されない",
            "外部委託・クラウドサービスが適用範囲に含まれていない",
        ],
        check_questions=[
            "AIMSの適用範囲は文書化されていますか？",
            "対象となるAIシステムが明確にリストされていますか？",
            "適用範囲は最新の状態に維持されていますか？",
        ],
        meti_mapping=["C07-R02"],
        nist_mapping=["GOVERN-1.2"],
        eu_ai_act_mapping=[],
    ),

    # ── 4.4 AIマネジメントシステム ──
    DetailedRequirement(
        req_id="ISO-4.4",
        clause="4.4",
        title="AIマネジメントシステム",
        description="ISO 42001の要求事項に従い、AIMSを確立・実施・維持・継続的に改善すること。",
        controls=[
            _CONTROL_MAP["A.2.2"],
            _CONTROL_MAP["A.4.4"],
        ],
        implementation_guidance=[
            "AIMSの全体構造と各要素間の関係を定義する",
            "PDCAサイクルをAIMSに組み込む",
            "AIMSを組織の他のマネジメントシステム（ISO 27001等）と統合する",
        ],
        evidence_examples=[
            "AIMSマニュアル（全体構成図含む）",
            "プロセスフロー図",
            "年間計画・改善計画",
        ],
        common_gaps=[
            "AIMSが文書のみで実際の運用に落とし込まれていない",
            "他のマネジメントシステムとの統合が不十分",
            "PDCAが1サイクルも回っていない",
        ],
        check_questions=[
            "AIMSは文書化され、関係者に周知されていますか？",
            "AIMSのPDCAサイクルは機能していますか？",
            "AIMSは他のマネジメントシステム（ISO 27001等）と統合されていますか？",
        ],
        meti_mapping=["C07-R02", "C07-R04"],
        nist_mapping=["GOVERN-1.1", "GOVERN-1.2"],
        eu_ai_act_mapping=["Art.9"],
    ),

    # ── 5.1 リーダーシップ及びコミットメント ──
    DetailedRequirement(
        req_id="ISO-5.1",
        clause="5.1",
        title="リーダーシップ及びコミットメント",
        description="トップマネジメントがAIMSに対するリーダーシップ及びコミットメントを実証すること。",
        controls=[
            _CONTROL_MAP["A.2.2"],
            _CONTROL_MAP["A.3.2"],
        ],
        implementation_guidance=[
            "経営会議でAIガバナンスを定期的な議題とする",
            "AIガバナンスに必要なリソース（人材・予算・ツール）を確保する",
            "トップマネジメントがAI方針を承認し、組織内外に発信する",
            "AIガバナンスのKPIを設定し、経営層がレビューする",
        ],
        evidence_examples=[
            "経営会議議事録（AIガバナンス議題を含む）",
            "AI関連予算の承認記録",
            "トップマネジメントのコミットメント声明",
            "AIガバナンスKPI報告書",
        ],
        common_gaps=[
            "AIガバナンスが現場任せで経営層の関与が薄い",
            "AIに関する予算・リソースが十分に確保されていない",
            "トップのコミットメントが形式的で実質的でない",
        ],
        check_questions=[
            "トップマネジメントはAIガバナンスに積極的に関与していますか？",
            "AIガバナンスに必要なリソースは確保されていますか？",
            "AIガバナンスのKPIは設定され、レビューされていますか？",
        ],
        meti_mapping=["C07-R01", "C07-R02"],
        nist_mapping=["GOVERN-1.1", "GOVERN-1.3"],
        eu_ai_act_mapping=["Art.9.1"],
    ),

    # ── 5.2 AI方針 ──
    DetailedRequirement(
        req_id="ISO-5.2",
        clause="5.2",
        title="AI方針",
        description="AIに関する方針を確立し、伝達し、利用可能な状態にすること。",
        controls=[
            _CONTROL_MAP["A.2.2"],
        ],
        implementation_guidance=[
            "AI方針には目的、適用範囲、原則、責任を含める",
            "AI方針は組織の事業戦略及びリスクアペタイトと整合させる",
            "全従業員がアクセス可能な形で公開する",
            "AI方針は最低年1回レビューし、必要に応じて改定する",
        ],
        evidence_examples=[
            "AI方針文書（承認日・承認者付き）",
            "方針の社内周知記録（イントラネット掲載、メール送信等）",
            "方針レビュー記録",
        ],
        common_gaps=[
            "AI方針が一般的すぎて組織固有の内容が含まれていない",
            "方針が策定されたが周知されていない",
            "方針が古く、最新の規制動向を反映していない",
        ],
        check_questions=[
            "AI方針は文書化され、トップマネジメントに承認されていますか？",
            "AI方針は全従業員に周知されていますか？",
            "AI方針は定期的にレビューされていますか？",
        ],
        meti_mapping=["C01-R01", "C07-R02"],
        nist_mapping=["GOVERN-1.1", "GOVERN-1.2"],
        eu_ai_act_mapping=["Art.9.1"],
    ),

    # ── 5.3 組織の役割、責任及び権限 ──
    DetailedRequirement(
        req_id="ISO-5.3",
        clause="5.3",
        title="組織の役割、責任及び権限",
        description="AIMS関連の役割に対して責任及び権限を割り当て、伝達すること。",
        controls=[
            _CONTROL_MAP["A.3.2"],
        ],
        implementation_guidance=[
            "AIガバナンス組織図を作成する",
            "RACI（Responsible/Accountable/Consulted/Informed）マトリクスを定義する",
            "役割には適切な権限（予算、意思決定、停止権限等）を付与する",
        ],
        evidence_examples=[
            "AIガバナンス組織図",
            "RACIマトリクス",
            "役割・責任の任命文書",
            "職務記述書（AIガバナンス関連の責務を含む）",
        ],
        common_gaps=[
            "AIガバナンスの責任者が形式的で権限が不十分",
            "データサイエンスチームとガバナンスチームの責任分担が不明確",
            "AIシステムのオーナーシップが不明確",
        ],
        check_questions=[
            "AIガバナンスに関する役割・責任は明確に定義されていますか？",
            "責任者には十分な権限が付与されていますか？",
            "役割・責任は組織内に周知されていますか？",
        ],
        meti_mapping=["C07-R01"],
        nist_mapping=["GOVERN-1.3", "GOVERN-2.1"],
        eu_ai_act_mapping=["Art.9.1"],
    ),

    # ── 6.1 リスク及び機会への取組み ──
    DetailedRequirement(
        req_id="ISO-6.1",
        clause="6.1",
        title="リスク及び機会への取組み",
        description="AIに関連するリスク及び機会を特定し、それらに対処するための計画を策定すること。",
        controls=[
            _CONTROL_MAP["A.6.2"],
        ],
        implementation_guidance=[
            "AIリスクを体系的に特定するフレームワーク（NIST AI RMF等）を採用する",
            "リスクと機会の両面を評価する（リスクのみに偏らない）",
            "リスク許容基準を定義し、経営層の承認を得る",
            "リスク及び機会への対処計画を策定し、実施責任者を決定する",
        ],
        evidence_examples=[
            "AIリスク・機会の一覧表",
            "リスク許容基準の文書",
            "対処計画と実施状況の記録",
        ],
        common_gaps=[
            "AIリスクの特定が技術面のみで、倫理・社会面が不足",
            "リスク許容基準が定義されていない",
            "リスクの「機会」の側面が評価されていない",
        ],
        check_questions=[
            "AIに関するリスクと機会を体系的に特定していますか？",
            "リスク許容基準は定義され、経営層に承認されていますか？",
            "対処計画は策定され、実施されていますか？",
        ],
        meti_mapping=["C02-R01"],
        nist_mapping=["MAP-1.1", "MAP-1.2", "MEASURE-1.1"],
        eu_ai_act_mapping=["Art.9.2"],
    ),

    # ── 6.1.2 AIリスクアセスメント ──
    DetailedRequirement(
        req_id="ISO-6.1.2",
        clause="6.1.2",
        title="AIリスクアセスメント",
        description="AIシステムに関するリスクアセスメントのプロセスを定義し、実施すること。",
        controls=[
            _CONTROL_MAP["A.6.2"],
        ],
        implementation_guidance=[
            "リスクアセスメント方法論を選定し文書化する（定性的/定量的/混合）",
            "AI固有のリスクカテゴリを定義する（バイアス、ドリフト、敵対的攻撃等）",
            "影響度×発生確率のリスクマトリクスを作成する",
            "リスクアセスメントの実施頻度と契機（新規導入、重大変更等）を定義する",
        ],
        evidence_examples=[
            "リスクアセスメント方法論の文書",
            "リスクアセスメント結果報告書",
            "リスクマトリクス",
            "リスクレジスタ（リスク台帳）",
        ],
        common_gaps=[
            "AI固有のリスク（バイアス、ドリフト等）が一般的なITリスクと混同されている",
            "定量的なリスク評価ができていない",
            "リスクアセスメントが初期導入時のみで定期的に更新されない",
        ],
        check_questions=[
            "AI固有のリスクカテゴリを定義していますか？",
            "リスクアセスメントの方法論は文書化されていますか？",
            "リスクアセスメントは定期的に実施されていますか？",
        ],
        meti_mapping=["C02-R01", "C02-R02"],
        nist_mapping=["MAP-2.1", "MAP-2.2", "MAP-3.1", "MEASURE-2.1"],
        eu_ai_act_mapping=["Art.9.2", "Art.9.5"],
    ),

    # ── 6.1.3 AIリスク対応 ──
    DetailedRequirement(
        req_id="ISO-6.1.3",
        clause="6.1.3",
        title="AIリスク対応",
        description="リスクアセスメントの結果に基づき、リスク対応の選択肢を選び、実施すること。",
        controls=[],
        implementation_guidance=[
            "リスク対応の4つの選択肢（回避・軽減・移転・受容）を検討する",
            "残留リスクを評価し、リスクオーナーの承認を得る",
            "リスク対応計画の実施状況をモニタリングする",
        ],
        evidence_examples=[
            "リスク対応計画書",
            "残留リスクの承認記録",
            "リスク対応の実施記録",
        ],
        common_gaps=[
            "リスク対応が「軽減」のみで、他の選択肢が検討されていない",
            "残留リスクが評価されていない",
            "リスク対応の効果測定が行われていない",
        ],
        check_questions=[
            "各リスクに対する対応方針は決定されていますか？",
            "残留リスクはリスクオーナーに承認されていますか？",
            "リスク対応の効果は測定されていますか？",
        ],
        meti_mapping=["C02-R01", "C02-R03"],
        nist_mapping=["MANAGE-1.1", "MANAGE-2.1", "MANAGE-2.2"],
        eu_ai_act_mapping=["Art.9.2", "Art.9.4"],
    ),

    # ── 6.2 AI目的及び達成計画 ──
    DetailedRequirement(
        req_id="ISO-6.2",
        clause="6.2",
        title="AI目的及びそれを達成するための計画策定",
        description="AIに関する測定可能な目的を設定し、達成計画を策定すること。",
        controls=[],
        implementation_guidance=[
            "AI目的はSMART基準で設定する（Specific, Measurable, Achievable, Relevant, Time-bound）",
            "AI方針との整合性を確認する",
            "達成計画には責任者、期限、必要リソース、マイルストーンを含める",
        ],
        evidence_examples=[
            "AI目的一覧（KPI含む）",
            "達成計画書",
            "進捗報告書",
        ],
        common_gaps=[
            "AI目的が曖昧で測定可能でない",
            "達成計画に具体的なマイルストーンがない",
            "進捗レビューが不定期",
        ],
        check_questions=[
            "AI目的は測定可能な形で設定されていますか？",
            "達成計画には責任者と期限が明記されていますか？",
            "目的の達成状況は定期的にレビューされていますか？",
        ],
        meti_mapping=["C10-R01"],
        nist_mapping=["GOVERN-1.1"],
        eu_ai_act_mapping=[],
    ),

    # ── 7.1 資源 ──
    DetailedRequirement(
        req_id="ISO-7.1",
        clause="7.1",
        title="資源",
        description="AIMSに必要な資源を決定し、提供すること。",
        controls=[
            _CONTROL_MAP["A.4.3"],
        ],
        implementation_guidance=[
            "人的資源（AI専門家、データサイエンティスト、ガバナンス担当等）の確保",
            "技術的資源（計算環境、ツール、インフラ）の確保",
            "財務的資源（予算の確保と承認）",
            "外部リソース（コンサルタント、教育機関等）の活用計画",
        ],
        evidence_examples=[
            "AI関連の人員計画",
            "AI関連予算書",
            "技術インフラ構成図",
            "外部委託契約書",
        ],
        common_gaps=[
            "AI専門人材の不足が認識されていない",
            "AIガバナンス活動の予算が不十分",
            "外部委託先の品質管理が不十分",
        ],
        check_questions=[
            "AIMSに必要な人的・技術的・財務的資源は確保されていますか？",
            "リソースの過不足は定期的にレビューされていますか？",
        ],
        meti_mapping=["C07-R02"],
        nist_mapping=["GOVERN-1.3", "GOVERN-2.1"],
        eu_ai_act_mapping=["Art.9.1"],
    ),

    # ── 7.2 力量 ──
    DetailedRequirement(
        req_id="ISO-7.2",
        clause="7.2",
        title="力量",
        description="AIMS関連の業務を行う人々に必要な力量を決定し、確保すること。",
        controls=[
            _CONTROL_MAP["A.7.2"],
        ],
        implementation_guidance=[
            "役割別の力量要件を定義する（技術/管理/利用者）",
            "力量の評価方法を確立する（テスト、実技、ポートフォリオ等）",
            "ギャップがある場合は教育・訓練・採用・外部委託で対処する",
            "力量の記録を維持する",
        ],
        evidence_examples=[
            "力量要件マトリクス",
            "教育訓練計画・実施記録",
            "力量評価結果",
            "資格・認定証の記録",
        ],
        common_gaps=[
            "AI固有の力量要件が定義されていない",
            "教育訓練が一回きりで継続的でない",
            "力量評価が形式的",
        ],
        check_questions=[
            "AIに関する力量要件は役割別に定義されていますか？",
            "必要な教育・訓練は計画的に実施されていますか？",
            "力量の記録は維持されていますか？",
        ],
        meti_mapping=["C08-R01"],
        nist_mapping=["GOVERN-2.2"],
        eu_ai_act_mapping=["Art.9.9"],
    ),

    # ── 7.3 認識 ──
    DetailedRequirement(
        req_id="ISO-7.3",
        clause="7.3",
        title="認識",
        description="関連する人々がAI方針、自らの貢献、不適合の影響を認識すること。",
        controls=[
            _CONTROL_MAP["A.7.3"],
        ],
        implementation_guidance=[
            "AIに関する意識向上プログラムを策定する",
            "AI方針、関連ルール、リスクについて定期的に啓発する",
            "不適合が発生した場合の影響（事業・個人への影響）を周知する",
        ],
        evidence_examples=[
            "意識向上プログラムの計画と実施記録",
            "研修出席記録",
            "理解度テスト結果",
        ],
        common_gaps=[
            "AI方針が存在するが現場レベルで認識されていない",
            "意識向上活動が初回のみで継続されていない",
        ],
        check_questions=[
            "従業員はAI方針の内容を理解していますか？",
            "AIMSへの自らの貢献を認識していますか？",
            "不適合の影響について認識していますか？",
        ],
        meti_mapping=["C08-R01", "C08-R02"],
        nist_mapping=["GOVERN-2.2"],
        eu_ai_act_mapping=["Art.9.9"],
    ),

    # ── 7.4 コミュニケーション ──
    DetailedRequirement(
        req_id="ISO-7.4",
        clause="7.4",
        title="コミュニケーション",
        description="AIMSに関する内部及び外部のコミュニケーションを計画すること。",
        controls=[],
        implementation_guidance=[
            "コミュニケーション計画（対象・内容・頻度・手段）を策定する",
            "内部コミュニケーション: AIガバナンス委員会報告、社内ニュースレター等",
            "外部コミュニケーション: 規制当局報告、顧客向け情報開示、IR等",
        ],
        evidence_examples=[
            "コミュニケーション計画書",
            "社内報告資料",
            "外部開示資料",
            "ステークホルダーへの情報提供記録",
        ],
        common_gaps=[
            "外部コミュニケーションの計画が不足",
            "インシデント時のコミュニケーション手順が未策定",
        ],
        check_questions=[
            "AIMSに関するコミュニケーション計画がありますか？",
            "内部と外部の両方のコミュニケーションがカバーされていますか？",
        ],
        meti_mapping=["C06-R01"],
        nist_mapping=["GOVERN-1.5", "MAP-1.5"],
        eu_ai_act_mapping=["Art.13"],
    ),

    # ── 7.5 文書化した情報 ──
    DetailedRequirement(
        req_id="ISO-7.5",
        clause="7.5",
        title="文書化した情報",
        description="AIMSで必要な文書化した情報を作成・更新・管理すること。",
        controls=[
            _CONTROL_MAP["A.5.4"],
        ],
        implementation_guidance=[
            "文書管理手順（作成・レビュー・承認・改訂・保管・廃棄）を確立する",
            "文書の分類体系とアクセス制御を定義する",
            "バージョン管理を行い、変更履歴を記録する",
            "必須文書リスト（AIMSマニュアル、方針、手順書、記録等）を作成する",
        ],
        evidence_examples=[
            "文書管理手順書",
            "必須文書リストと保管状況",
            "文書のバージョン管理記録",
        ],
        common_gaps=[
            "文書が散在しており一元管理されていない",
            "バージョン管理が不十分で古い文書が使われている",
            "記録の保存期間が定義されていない",
        ],
        check_questions=[
            "AIMSに必要な文書は一覧化されていますか？",
            "文書管理手順（作成・承認・改訂・廃棄）は確立されていますか？",
            "バージョン管理が行われていますか？",
        ],
        meti_mapping=["C06-R03", "C07-R04"],
        nist_mapping=["GOVERN-1.4"],
        eu_ai_act_mapping=["Art.11", "Art.12"],
    ),

    # ── 8.1 運用の計画及び管理 ──
    DetailedRequirement(
        req_id="ISO-8.1",
        clause="8.1",
        title="運用の計画及び管理",
        description="AIMSの要求事項を満たすために必要なプロセスを計画・実施・管理すること。",
        controls=[
            _CONTROL_MAP["A.5.2"],
            _CONTROL_MAP["A.8.2"],
        ],
        implementation_guidance=[
            "AIシステムのライフサイクル管理プロセスを確立する",
            "変更管理プロセスを定義する（モデル更新、データ更新等）",
            "運用手順を文書化し、運用者に教育する",
            "外部委託プロセスの管理方法を定義する",
        ],
        evidence_examples=[
            "運用手順書",
            "変更管理記録",
            "外部委託管理計画",
            "運用レビュー記録",
        ],
        common_gaps=[
            "AIモデルの変更管理が通常のソフトウェア変更管理と分離されていない",
            "運用手順が暗黙知で文書化されていない",
        ],
        check_questions=[
            "AIシステムの運用手順は文書化されていますか？",
            "変更管理プロセスは確立されていますか？",
            "外部委託先の管理は適切に行われていますか？",
        ],
        meti_mapping=["C07-R02"],
        nist_mapping=["MANAGE-1.1", "MANAGE-2.1"],
        eu_ai_act_mapping=["Art.9.1"],
    ),

    # ── 8.2 AIリスクアセスメント（実施） ──
    DetailedRequirement(
        req_id="ISO-8.2",
        clause="8.2",
        title="AIリスクアセスメント（実施）",
        description="計画した間隔またはリスクの変化が生じた場合にAIリスクアセスメントを実施すること。",
        controls=[
            _CONTROL_MAP["A.6.2"],
        ],
        implementation_guidance=[
            "定期的なリスクアセスメントスケジュールを設定する（最低年1回）",
            "重大な変更（新モデル導入、データソース変更等）時に臨時アセスメントを実施する",
            "リスクアセスメント結果を記録し、前回結果との比較を行う",
        ],
        evidence_examples=[
            "リスクアセスメント実施記録",
            "リスクアセスメントスケジュール",
            "リスクの変化トレンド分析",
        ],
        common_gaps=[
            "リスクアセスメントが1回実施されたのみで更新されていない",
            "変更時のトリガー条件が定義されていない",
        ],
        check_questions=[
            "リスクアセスメントは計画的に実施されていますか？",
            "変更時のリスクアセスメント実施条件は定義されていますか？",
        ],
        meti_mapping=["C02-R01"],
        nist_mapping=["MEASURE-1.1", "MEASURE-2.1"],
        eu_ai_act_mapping=["Art.9.2"],
    ),

    # ── 8.3 AIリスク対応（実施） ──
    DetailedRequirement(
        req_id="ISO-8.3",
        clause="8.3",
        title="AIリスク対応（実施）",
        description="AIリスク対応計画を実施すること。",
        controls=[
            _CONTROL_MAP["A.8.3"],
        ],
        implementation_guidance=[
            "リスク対応計画に基づき、管理策を実装する",
            "管理策の有効性をテスト・評価する",
            "対応の実施状況と残留リスクを定期的に報告する",
        ],
        evidence_examples=[
            "管理策の実装記録",
            "有効性テスト結果",
            "残留リスク報告",
        ],
        common_gaps=[
            "リスク対応計画はあるが実装が遅延している",
            "管理策の有効性が検証されていない",
        ],
        check_questions=[
            "リスク対応計画は予定通り実施されていますか？",
            "管理策の有効性は検証されていますか？",
        ],
        meti_mapping=["C02-R03", "C05-R01"],
        nist_mapping=["MANAGE-2.1", "MANAGE-2.2"],
        eu_ai_act_mapping=["Art.9.4"],
    ),

    # ── 8.4 AIシステム影響評価 ──
    DetailedRequirement(
        req_id="ISO-8.4",
        clause="8.4",
        title="AIシステム影響評価",
        description="AIシステムが個人、グループ、社会に与える影響を評価すること。",
        controls=[
            _CONTROL_MAP["A.6.2"],
            _CONTROL_MAP["A.5.3"],
        ],
        implementation_guidance=[
            "影響評価の方法論と実施基準を定義する",
            "人権影響評価（HRIA）を含める",
            "影響の範囲（直接/間接、短期/長期）を考慮する",
            "影響評価結果に基づき軽減措置を策定・実施する",
        ],
        evidence_examples=[
            "AIシステム影響評価報告書",
            "人権影響評価結果",
            "軽減措置の実施記録",
        ],
        common_gaps=[
            "影響評価が技術的性能のみに焦点を当て、社会的影響を見落とす",
            "間接的な影響が評価されていない",
            "影響評価の結果が軽減措置に反映されていない",
        ],
        check_questions=[
            "AIシステムの社会的影響（人権、公平性、環境等）を評価していますか？",
            "影響評価の結果は軽減措置に反映されていますか？",
            "影響評価は定期的に更新されていますか？",
        ],
        meti_mapping=["C01-R01", "C03-R01", "C04-R02"],
        nist_mapping=["MAP-2.1", "MAP-2.2", "MAP-5.1"],
        eu_ai_act_mapping=["Art.9.2", "Art.27"],
    ),

    # ── 9.1 監視、測定、分析及び評価 ──
    DetailedRequirement(
        req_id="ISO-9.1",
        clause="9.1",
        title="監視、測定、分析及び評価",
        description="AIMSのパフォーマンスを監視・測定・分析・評価すること。",
        controls=[
            _CONTROL_MAP["A.8.2"],
        ],
        implementation_guidance=[
            "監視・測定の対象を定義する（AIシステム性能、ガバナンスKPI等）",
            "監視・測定の方法、頻度、責任者を決定する",
            "結果を分析し、改善のための情報として活用する",
        ],
        evidence_examples=[
            "KPIダッシュボード",
            "性能モニタリング報告書",
            "分析・評価レポート",
        ],
        common_gaps=[
            "モニタリング対象がAIシステムの技術指標のみでガバナンスKPIを含まない",
            "分析結果が改善活動に結びついていない",
        ],
        check_questions=[
            "AIMSのパフォーマンス指標は定義されていますか？",
            "モニタリング結果は定期的に分析・評価されていますか？",
        ],
        meti_mapping=["C03-R02", "C07-R04"],
        nist_mapping=["MEASURE-1.1", "MEASURE-3.1"],
        eu_ai_act_mapping=["Art.9.7", "Art.72"],
    ),

    # ── 9.2 内部監査 ──
    DetailedRequirement(
        req_id="ISO-9.2",
        clause="9.2",
        title="内部監査",
        description="計画した間隔でAIMSの内部監査を実施すること。",
        controls=[],
        implementation_guidance=[
            "内部監査プログラムを策定する（頻度、範囲、方法、監査員）",
            "監査員はAI/AIMSに関する力量を持つこと",
            "監査の独立性を確保する（自分の業務を自分で監査しない）",
            "監査結果を文書化し、是正措置を追跡する",
        ],
        evidence_examples=[
            "内部監査プログラム",
            "内部監査報告書",
            "監査員の力量記録",
            "是正措置の実施・完了記録",
        ],
        common_gaps=[
            "AI固有の監査項目が不足（一般的なITセキュリティ監査のみ）",
            "監査員にAI/MLの知識が不足",
            "是正措置が実施されず放置されている",
        ],
        check_questions=[
            "内部監査プログラムはAI固有の項目を含んでいますか？",
            "監査員はAIMSについて適切な力量を持っていますか？",
            "監査で指摘された事項は是正されていますか？",
        ],
        meti_mapping=["C07-R04"],
        nist_mapping=["GOVERN-1.4", "MEASURE-3.1"],
        eu_ai_act_mapping=["Art.9.8"],
    ),

    # ── 9.3 マネジメントレビュー ──
    DetailedRequirement(
        req_id="ISO-9.3",
        clause="9.3",
        title="マネジメントレビュー",
        description="計画した間隔でAIMSのマネジメントレビューを実施すること。",
        controls=[],
        implementation_guidance=[
            "最低年1回、マネジメントレビューを実施する",
            "レビューのインプット: 監査結果、KPI、リスクの変化、改善機会等",
            "レビューのアウトプット: 改善指示、リソース配分、方針変更等",
            "トップマネジメントの参加を確保する",
        ],
        evidence_examples=[
            "マネジメントレビュー議事録",
            "レビューインプット資料",
            "改善指示と実施状況",
        ],
        common_gaps=[
            "マネジメントレビューが形式的で実質的な議論がない",
            "レビュー結果の改善指示が追跡されていない",
            "トップマネジメントが実質的に参加していない",
        ],
        check_questions=[
            "マネジメントレビューは定期的に実施されていますか？",
            "トップマネジメントは実質的に参加していますか？",
            "レビュー結果に基づく改善指示は追跡されていますか？",
        ],
        meti_mapping=["C07-R02"],
        nist_mapping=["GOVERN-1.4"],
        eu_ai_act_mapping=["Art.9.8"],
    ),

    # ── 10.1 不適合及び是正処置 ──
    DetailedRequirement(
        req_id="ISO-10.1",
        clause="10.1",
        title="不適合及び是正処置",
        description="不適合が発生した場合、是正処置を講じること。",
        controls=[
            _CONTROL_MAP["A.8.3"],
        ],
        implementation_guidance=[
            "不適合の検出・記録・分類プロセスを確立する",
            "根本原因分析（RCA）を実施する",
            "是正処置を策定・実施し、有効性を確認する",
            "再発防止策を講じる",
        ],
        evidence_examples=[
            "不適合報告書",
            "根本原因分析記録",
            "是正処置の実施・有効性確認記録",
            "再発防止策の文書",
        ],
        common_gaps=[
            "不適合が報告されず把握できていない",
            "根本原因分析が浅い（表面的な対処のみ）",
            "是正処置の有効性が確認されていない",
        ],
        check_questions=[
            "不適合を報告・記録するプロセスがありますか？",
            "不適合に対して根本原因分析を実施していますか？",
            "是正処置の有効性は確認されていますか？",
        ],
        meti_mapping=["C03-R03", "C05-R03"],
        nist_mapping=["MANAGE-3.1", "MANAGE-4.1"],
        eu_ai_act_mapping=["Art.9.4", "Art.72"],
    ),

    # ── 10.2 継続的改善 ──
    DetailedRequirement(
        req_id="ISO-10.2",
        clause="10.2",
        title="継続的改善",
        description="AIMSの適切性、妥当性及び有効性を継続的に改善すること。",
        controls=[],
        implementation_guidance=[
            "改善の機会を体系的に特定するプロセスを確立する",
            "改善計画を策定し、優先順位付けする",
            "改善の実施と効果を測定・記録する",
            "ベンチマーク（業界標準・先進企業との比較）を活用する",
        ],
        evidence_examples=[
            "改善計画と実施記録",
            "改善効果の測定結果",
            "ベンチマーク分析結果",
            "PDCAサイクルの回転記録",
        ],
        common_gaps=[
            "「継続的改善」が掛け声のみで具体的な仕組みがない",
            "改善が場当たり的で体系的でない",
            "改善の効果が測定されていない",
        ],
        check_questions=[
            "改善の機会を体系的に特定するプロセスがありますか？",
            "改善計画は策定され、実施されていますか？",
            "改善の効果は測定されていますか？",
        ],
        meti_mapping=["C10-R01"],
        nist_mapping=["GOVERN-1.4", "MANAGE-4.1"],
        eu_ai_act_mapping=["Art.9.8"],
    ),
]


# ── ユーティリティ ────────────────────────────────────────────────

_DETAILED_MAP: dict[str, DetailedRequirement] = {
    r.req_id: r for r in DETAILED_REQUIREMENTS
}


def get_detailed_requirement(req_id: str) -> DetailedRequirement | None:
    """要求事項IDから詳細要求事項を取得."""
    return _DETAILED_MAP.get(req_id)


def all_detailed_requirements() -> list[DetailedRequirement]:
    """全詳細要求事項をフラットなリストで返す."""
    return list(DETAILED_REQUIREMENTS)


def all_controls() -> list[Control]:
    """全管理策を返す."""
    return list(ANNEX_A_CONTROLS)


def get_control(control_id: str) -> Control | None:
    """管理策IDから管理策を取得."""
    return _CONTROL_MAP.get(control_id)


def get_check_questions_by_clause(clause: str) -> list[str]:
    """条項番号からチェック質問一覧を取得."""
    questions: list[str] = []
    for req in DETAILED_REQUIREMENTS:
        if req.clause.startswith(clause):
            questions.extend(req.check_questions)
    return questions


def get_common_gaps_all() -> list[dict[str, str]]:
    """全要求事項のCommon Gapsを取得."""
    result: list[dict[str, str]] = []
    for req in DETAILED_REQUIREMENTS:
        for gap in req.common_gaps:
            result.append({
                "req_id": req.req_id,
                "clause": req.clause,
                "title": req.title,
                "gap": gap,
            })
    return result
