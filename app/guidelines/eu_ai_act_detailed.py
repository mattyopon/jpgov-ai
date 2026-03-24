# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""EU AI Act 詳細リスク分類・義務要件定義.

EU AI Act (Regulation (EU) 2024/1689) の詳細なリスク分類と義務要件。
Annex III の高リスクAIシステム一覧、各リスクレベルの義務要件、
適合性評価手順、日本企業向けチェックリストを含む。

参考:
- Regulation (EU) 2024/1689 of the European Parliament and of the Council
  (EU Artificial Intelligence Act)
- EUR-Lex: https://eur-lex.europa.eu/eli/reg/2024/1689
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HighRiskUseCase:
    """高リスクAIユースケース (Annex III)."""

    use_case_id: str
    category: str
    category_number: int  # Annex III の番号 (1-8)
    description: str
    examples: list[str] = field(default_factory=list)
    key_obligations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskLevelDetail:
    """リスクレベル別の詳細義務要件."""

    level: str  # "unacceptable", "high", "limited", "minimal"
    title: str
    description: str
    obligations: list[str] = field(default_factory=list)
    articles: list[str] = field(default_factory=list)  # 関連条文


@dataclass(frozen=True)
class ConformityStep:
    """適合性評価ステップ."""

    step_number: int
    title: str
    description: str
    required_documents: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JapanCompanyCheckItem:
    """日本企業向けチェックリスト項目."""

    check_id: str
    category: str  # "scope", "classification", "obligation", "technical", "documentation"
    question: str
    guidance: str
    applicable_roles: list[str] = field(default_factory=list)  # "provider", "deployer", "importer"
    meti_mapping: list[str] = field(default_factory=list)
    iso_mapping: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# リスクレベル詳細
# ---------------------------------------------------------------------------

RISK_LEVELS: list[RiskLevelDetail] = [
    RiskLevelDetail(
        level="unacceptable",
        title="許容不可リスク（Unacceptable Risk）",
        description="基本的権利に対する明白な脅威をもたらすAIシステム。全面禁止。",
        obligations=[
            "市場投入・利用の全面禁止",
            "ソーシャルスコアリング（政府による社会的評点付け）の禁止",
            "リアルタイム遠隔生体認証の原則禁止（法執行の限定的例外あり）",
            "感情認識を用いた搾取的行為の禁止",
            "無差別な顔画像スクレイピングによるデータベース構築の禁止",
            "サブリミナル技術による操作の禁止",
            "脆弱な集団の脆弱性を悪用する行為の禁止",
        ],
        articles=["Art.5"],
    ),
    RiskLevelDetail(
        level="high",
        title="高リスク（High Risk）",
        description=(
            "人の安全または基本的権利に重大な影響を及ぼす可能性のあるAIシステム。"
            "Annex III に列挙されたカテゴリに該当するシステム。"
        ),
        obligations=[
            "リスク管理システムの確立・維持（Art.9）",
            "データガバナンス: 学習・検証・テストデータの品質確保（Art.10）",
            "技術文書の作成（Art.11）",
            "ログ記録（自動ロギング機能の実装）（Art.12）",
            "透明性: ユーザーへの適切な情報提供（Art.13）",
            "人間による監視（Human Oversight）の確保（Art.14）",
            "精度・堅牢性・サイバーセキュリティの確保（Art.15）",
            "適合性評価（Conformity Assessment）の実施（Art.43）",
            "EU適合宣言（EU Declaration of Conformity）の作成（Art.47）",
            "CEマーキングの貼付（Art.48）",
            "EU域内の代理人の選任（EU域外事業者の場合）（Art.22）",
            "品質管理システムの構築（Art.17）",
            "市場投入後のモニタリング計画の策定（Art.72）",
            "重大インシデントの報告（Art.73）",
        ],
        articles=[
            "Art.6", "Art.9", "Art.10", "Art.11", "Art.12", "Art.13",
            "Art.14", "Art.15", "Art.17", "Art.22", "Art.43", "Art.47",
            "Art.48", "Art.72", "Art.73",
        ],
    ),
    RiskLevelDetail(
        level="limited",
        title="限定的リスク（Limited Risk）",
        description="透明性の義務が課されるAIシステム（チャットボット、感情認識等）。",
        obligations=[
            "AIシステムとのやり取りであることの通知（Art.50.1）",
            "感情認識システム利用の通知（Art.50.3）",
            "ディープフェイクであることの明示（Art.50.4）",
            "AI生成コンテンツの明示（Art.50.2）",
        ],
        articles=["Art.50"],
    ),
    RiskLevelDetail(
        level="minimal",
        title="最小リスク（Minimal Risk）",
        description="上記以外のAIシステム。特段の規制義務なし。自主的行動規範の策定を推奨。",
        obligations=[
            "特段の法的義務なし",
            "自主的行動規範（Codes of Conduct）の策定を推奨（Art.95）",
            "AIリテラシーの確保は全リスクレベルに適用（Art.4）",
        ],
        articles=["Art.4", "Art.95"],
    ),
]

# ---------------------------------------------------------------------------
# Annex III 高リスクAIシステム一覧（8カテゴリ）
# ---------------------------------------------------------------------------

ANNEX_III_HIGH_RISK: list[HighRiskUseCase] = [
    # ── 1. 生体認証・カテゴリ分類 ──
    HighRiskUseCase(
        use_case_id="ANNEX3-1",
        category="生体認証（Biometrics）",
        category_number=1,
        description="自然人の生体認証に使用されるAIシステム（遠隔生体認証を含む）。",
        examples=[
            "リアルタイム遠隔生体認証システム",
            "事後的遠隔生体認証システム",
            "感情認識システム",
            "生体データに基づくカテゴリ分類システム",
        ],
        key_obligations=[
            "基本的権利影響評価の実施（Art.27）",
            "国家監督当局への登録",
            "リアルタイム遠隔生体認証は法執行の特定条件下のみ許可",
        ],
    ),
    # ── 2. 重要インフラ ──
    HighRiskUseCase(
        use_case_id="ANNEX3-2",
        category="重要インフラ（Critical Infrastructure）",
        category_number=2,
        description="重要なデジタルインフラ、交通、水・ガス・暖房・電力の供給における安全コンポーネントとしてのAI。",
        examples=[
            "道路交通の安全コンポーネント",
            "水・ガス・暖房・電力供給の管理",
            "デジタルインフラの安全管理",
        ],
        key_obligations=[
            "安全性に関する既存のEU調和法規への追加準拠",
            "リスク管理システムの確立",
            "品質管理体制の構築",
        ],
    ),
    # ── 3. 教育・職業訓練 ──
    HighRiskUseCase(
        use_case_id="ANNEX3-3",
        category="教育・職業訓練（Education and Vocational Training）",
        category_number=3,
        description="教育・職業訓練へのアクセスと成績評価に影響するAIシステム。",
        examples=[
            "教育機関の入学選考を決定・実質的に影響するAI",
            "学習者のレベル評価・試験採点を行うAI",
            "学習者の行動監視・不正検知AI",
            "適応学習システムによる学習パス決定",
        ],
        key_obligations=[
            "入学選考AIは適合性評価（第三者評価）が必要",
            "人間による監視の確保",
            "バイアスのない評価の保証",
        ],
    ),
    # ── 4. 雇用・労働者管理 ──
    HighRiskUseCase(
        use_case_id="ANNEX3-4",
        category="雇用・労働者管理（Employment, Workers Management）",
        category_number=4,
        description="雇用、労働者管理、自営業へのアクセスに関するAIシステム。",
        examples=[
            "採用・選考における候補者の選別・フィルタリング",
            "求人広告のターゲティング",
            "応募書類の選考・評価",
            "面接・テストの評価",
            "従業員の業績評価",
            "昇進・解雇の意思決定支援",
            "タスク割り当ての最適化",
            "労働者の行動監視",
        ],
        key_obligations=[
            "公平性指標の継続的モニタリング",
            "雇用差別法への準拠の確認",
            "従業員への通知義務",
        ],
    ),
    # ── 5. 重要な公共・民間サービスへのアクセス ──
    HighRiskUseCase(
        use_case_id="ANNEX3-5",
        category="重要な公共・民間サービスへのアクセス（Essential Services）",
        category_number=5,
        description="重要な公共・民間サービスへのアクセスと享受に関するAIシステム。",
        examples=[
            "公的扶助・社会保障の受給資格判定",
            "信用スコアリング（自然人の信用度評価）",
            "保険料の算定（生命保険・医療保険）",
            "緊急通報のトリアージ・優先順位付け",
            "緊急車両の派遣決定",
        ],
        key_obligations=[
            "基本的権利影響評価の実施",
            "信用スコアリングは第三者適合性評価が必要",
            "決定に対する異議申立て手段の確保",
        ],
    ),
    # ── 6. 法執行 ──
    HighRiskUseCase(
        use_case_id="ANNEX3-6",
        category="法執行（Law Enforcement）",
        category_number=6,
        description="法執行機関が使用するAIシステム。",
        examples=[
            "証拠の信頼性評価",
            "ポリグラフ・類似ツール",
            "犯罪分析における個人の評価",
            "犯罪予測（プロファイリング）",
            "犯罪捜査における顔・指紋等のマッチング",
        ],
        key_obligations=[
            "基本的権利影響評価の実施",
            "国家監督当局への登録",
            "人間による監視の厳格な確保",
        ],
    ),
    # ── 7. 移民・亡命・国境管理 ──
    HighRiskUseCase(
        use_case_id="ANNEX3-7",
        category="移民・亡命・国境管理（Migration, Asylum and Border Control）",
        category_number=7,
        description="移民・亡命・国境管理に使用されるAIシステム。",
        examples=[
            "ポリグラフ・類似ツール",
            "セキュリティリスク評価",
            "不法入国リスクの評価",
            "査証申請の審査支援",
            "亡命申請の審査支援",
        ],
        key_obligations=[
            "基本的権利影響評価の実施",
            "国家監督当局への登録",
        ],
    ),
    # ── 8. 司法・民主主義プロセス ──
    HighRiskUseCase(
        use_case_id="ANNEX3-8",
        category="司法・民主主義プロセス（Administration of Justice and Democratic Processes）",
        category_number=8,
        description="司法行政及び民主主義プロセスに影響するAIシステム。",
        examples=[
            "事実・法律の調査・解釈の支援",
            "個別事案への法適用の支援",
            "裁判外紛争解決",
            "選挙結果への影響を与えるシステム（投票行動への影響を含む）",
        ],
        key_obligations=[
            "司法の独立性への配慮",
            "人間による最終判断の確保",
            "民主主義プロセスの完全性の保護",
        ],
    ),
]

# ---------------------------------------------------------------------------
# 適合性評価（Conformity Assessment）手順
# ---------------------------------------------------------------------------

CONFORMITY_ASSESSMENT_STEPS: list[ConformityStep] = [
    ConformityStep(
        step_number=1,
        title="対象確認",
        description="AIシステムが高リスクに該当するか（Art.6 + Annex III）を確認する。",
        required_documents=[
            "AIシステムの用途・機能の記述書",
            "リスク分類の根拠文書",
        ],
    ),
    ConformityStep(
        step_number=2,
        title="適合性評価手続きの選択",
        description=(
            "内部統制に基づく適合性評価（Annex VI）または第三者適合性評価（Annex VII）を選択する。"
            "特定のカテゴリ（生体認証、重要インフラ等）は第三者評価が必須。"
        ),
        required_documents=[
            "適合性評価手続きの選択根拠",
            "第三者評価が必要な場合: 認定評価機関への申請書",
        ],
    ),
    ConformityStep(
        step_number=3,
        title="技術文書の作成",
        description="Art.11 及び Annex IV に基づく技術文書を作成する。",
        required_documents=[
            "AIシステムの一般的な説明",
            "設計仕様の詳細",
            "開発プロセスの記述",
            "監視・テスト・検証の方法と結果",
            "リスク管理に関する詳細情報",
            "変更管理の記録",
        ],
    ),
    ConformityStep(
        step_number=4,
        title="品質管理システムの確立",
        description="Art.17 に基づく品質管理システムを確立する。",
        required_documents=[
            "品質管理システムの方針と手順",
            "設計管理手順",
            "データ管理手順",
            "市場投入後モニタリング計画",
        ],
    ),
    ConformityStep(
        step_number=5,
        title="適合性評価の実施",
        description="選択した手続きに基づき適合性評価を実施する。",
        required_documents=[
            "適合性評価報告書",
            "テスト結果・検証結果",
            "第三者評価の場合: 評価機関の報告書",
        ],
    ),
    ConformityStep(
        step_number=6,
        title="EU適合宣言の作成",
        description="Art.47 に基づくEU適合宣言（Declaration of Conformity）を作成する。",
        required_documents=[
            "EU適合宣言書",
            "署名者の権限証明",
        ],
    ),
    ConformityStep(
        step_number=7,
        title="CEマーキングの貼付",
        description="Art.48 に基づきCEマーキングを貼付する。",
        required_documents=[
            "CEマーキング貼付記録",
        ],
    ),
    ConformityStep(
        step_number=8,
        title="EU AIデータベースへの登録",
        description="Art.71 に基づきEU AIデータベースに登録する。",
        required_documents=[
            "登録申請書",
            "システム情報の登録確認書",
        ],
    ),
    ConformityStep(
        step_number=9,
        title="市場投入後のモニタリング",
        description="Art.72 に基づく市場投入後のモニタリング計画を実施する。",
        required_documents=[
            "モニタリング計画書",
            "モニタリング結果の定期報告書",
            "重大インシデント報告（該当時）",
        ],
    ),
]

# ---------------------------------------------------------------------------
# 日本企業向けチェックリスト
# ---------------------------------------------------------------------------

JAPAN_COMPANY_CHECKLIST: list[JapanCompanyCheckItem] = [
    # ── スコープ確認 ──
    JapanCompanyCheckItem(
        check_id="EU-JP-01",
        category="scope",
        question="EU域内にAIシステムの出力を提供していますか？（直接または間接）",
        guidance=(
            "EU AI Actは、AIシステムのプロバイダーまたはデプロイヤーの所在地に関わらず、"
            "EU域内で使用されるAIシステムに適用される（Art.2）。"
            "日本からEU市場に提供するAIサービスも対象。"
        ),
        applicable_roles=["provider", "deployer"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-02",
        category="scope",
        question="EU域内にユーザーがいるAIサービスを提供していますか？",
        guidance=(
            "SaaS等のクラウドサービスでEU域内のユーザーが利用する場合も適用対象。"
        ),
        applicable_roles=["provider"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-03",
        category="scope",
        question="EU域内の事業者にAIコンポーネント（モデル、API等）を供給していますか？",
        guidance=(
            "EU域内の事業者が最終製品に組み込むAIコンポーネントを供給する場合、"
            "サプライチェーン上の義務が発生する可能性がある。"
        ),
        applicable_roles=["provider"],
    ),

    # ── リスク分類 ──
    JapanCompanyCheckItem(
        check_id="EU-JP-04",
        category="classification",
        question="AIシステムはAnnex III の高リスクカテゴリに該当しますか？",
        guidance=(
            "Annex III の8カテゴリ（生体認証、重要インフラ、教育、雇用、"
            "重要サービス、法執行、移民管理、司法）に該当する場合は高リスク。"
        ),
        applicable_roles=["provider", "deployer"],
        meti_mapping=["C02-R01"],
        iso_mapping=["ISO-6.1.2"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-05",
        category="classification",
        question="AIシステムはEU調和法規（Annex I）の対象製品の安全コンポーネントですか？",
        guidance=(
            "医療機器、機械、自動車等のEU調和法規の対象製品に"
            "AIを安全コンポーネントとして組み込む場合も高リスクに該当。"
        ),
        applicable_roles=["provider"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-06",
        category="classification",
        question="汎用AIモデル（GPAI）を提供していますか？",
        guidance=(
            "GPT-4等の汎用AIモデルには別途の規制（Art.51-56）が適用される。"
            "特にシステミックリスクを持つモデル（FLOPs基準等）には追加義務。"
        ),
        applicable_roles=["provider"],
    ),

    # ── 義務対応 ──
    JapanCompanyCheckItem(
        check_id="EU-JP-07",
        category="obligation",
        question="リスク管理システムは確立されていますか？（Art.9）",
        guidance=(
            "高リスクAIシステムのプロバイダーは、ライフサイクル全体にわたる"
            "リスク管理システムを確立・維持する義務がある。"
        ),
        applicable_roles=["provider"],
        meti_mapping=["C02-R01", "C02-R03"],
        iso_mapping=["ISO-6.1", "ISO-6.1.2"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-08",
        category="obligation",
        question="データガバナンスの要件を満たしていますか？（Art.10）",
        guidance=(
            "学習・検証・テストデータの品質管理、バイアス評価、"
            "データの代表性確認が必要。"
        ),
        applicable_roles=["provider"],
        meti_mapping=["C02-R02"],
        iso_mapping=["ISO-6.1.2"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-09",
        category="obligation",
        question="技術文書は作成・維持されていますか？（Art.11）",
        guidance="Art.11 + Annex IV に基づく包括的な技術文書が必要。",
        applicable_roles=["provider"],
        meti_mapping=["C06-R03"],
        iso_mapping=["ISO-7.5"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-10",
        category="obligation",
        question="自動ログ記録機能は実装されていますか？（Art.12）",
        guidance="AIシステムの動作に関する自動ログ記録機能の実装が必要。",
        applicable_roles=["provider"],
        meti_mapping=["C07-R04"],
        iso_mapping=["ISO-7.5"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-11",
        category="obligation",
        question="透明性要件を満たしていますか？（Art.13/Art.50）",
        guidance=(
            "高リスクAI: デプロイヤーが理解できる利用説明書の提供。"
            "限定的リスクAI: AIシステムとのやり取りであることの通知等。"
        ),
        applicable_roles=["provider", "deployer"],
        meti_mapping=["C06-R01", "C06-R02"],
        iso_mapping=["ISO-7.4"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-12",
        category="obligation",
        question="人間による監視（Human Oversight）の仕組みがありますか？（Art.14）",
        guidance=(
            "高リスクAIシステムには、人間が効果的に監視できる設計が必要。"
            "停止機能（stop button）の実装を含む。"
        ),
        applicable_roles=["provider", "deployer"],
        meti_mapping=["C01-R02"],
        iso_mapping=["ISO-8.4"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-13",
        category="obligation",
        question="精度・堅牢性・サイバーセキュリティの要件を満たしていますか？（Art.15）",
        guidance="精度指標の開示、堅牢性テスト、サイバーセキュリティ対策が必要。",
        applicable_roles=["provider"],
        meti_mapping=["C05-R01"],
        iso_mapping=["ISO-8.3"],
    ),

    # ── 技術的対応 ──
    JapanCompanyCheckItem(
        check_id="EU-JP-14",
        category="technical",
        question="EU域内代理人を選任していますか？（Art.22）",
        guidance=(
            "EU域外に所在するプロバイダーは、EU域内に代理人を選任し、"
            "書面による委任状を付与する必要がある。"
        ),
        applicable_roles=["provider"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-15",
        category="technical",
        question="適合性評価の準備は完了していますか？（Art.43）",
        guidance=(
            "内部統制（Annex VI）または第三者評価（Annex VII）の選択と準備。"
            "生体認証等の特定カテゴリは第三者評価が必須。"
        ),
        applicable_roles=["provider"],
        meti_mapping=["C07-R02"],
        iso_mapping=["ISO-9.2"],
    ),

    # ── 文書管理 ──
    JapanCompanyCheckItem(
        check_id="EU-JP-16",
        category="documentation",
        question="EU適合宣言の作成準備はできていますか？（Art.47）",
        guidance="EU適合宣言（Declaration of Conformity）の作成と維持が必要。",
        applicable_roles=["provider"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-17",
        category="documentation",
        question="市場投入後モニタリング計画はありますか？（Art.72）",
        guidance=(
            "AI-as-a-Serviceの場合も、市場投入後のモニタリングが必要。"
            "データドリフト、性能劣化、バイアスの変化を継続的に監視する。"
        ),
        applicable_roles=["provider"],
        meti_mapping=["C03-R02", "C07-R04"],
        iso_mapping=["ISO-9.1"],
    ),
    JapanCompanyCheckItem(
        check_id="EU-JP-18",
        category="documentation",
        question="重大インシデント報告の体制は整備されていますか？（Art.73）",
        guidance=(
            "高リスクAIシステムの重大インシデント（死亡、重傷、基本的権利侵害等）"
            "を所管当局に報告する義務がある。報告期限あり。"
        ),
        applicable_roles=["provider", "deployer"],
        meti_mapping=["C05-R03"],
        iso_mapping=["ISO-10.1"],
    ),
]


# ── ユーティリティ ────────────────────────────────────────────────

_RISK_LEVEL_MAP: dict[str, RiskLevelDetail] = {r.level: r for r in RISK_LEVELS}
_HIGH_RISK_MAP: dict[str, HighRiskUseCase] = {u.use_case_id: u for u in ANNEX_III_HIGH_RISK}
_CHECK_MAP: dict[str, JapanCompanyCheckItem] = {c.check_id: c for c in JAPAN_COMPANY_CHECKLIST}


def get_risk_level_detail(level: str) -> RiskLevelDetail | None:
    """リスクレベルから詳細を取得."""
    return _RISK_LEVEL_MAP.get(level)


def get_high_risk_use_case(use_case_id: str) -> HighRiskUseCase | None:
    """ユースケースIDから高リスクユースケースを取得."""
    return _HIGH_RISK_MAP.get(use_case_id)


def all_high_risk_use_cases() -> list[HighRiskUseCase]:
    """全高リスクユースケースを返す."""
    return list(ANNEX_III_HIGH_RISK)


def all_conformity_steps() -> list[ConformityStep]:
    """全適合性評価ステップを返す."""
    return list(CONFORMITY_ASSESSMENT_STEPS)


def all_japan_checklist_items() -> list[JapanCompanyCheckItem]:
    """全日本企業向けチェックリスト項目を返す."""
    return list(JAPAN_COMPANY_CHECKLIST)


def get_japan_checklist_by_category(category: str) -> list[JapanCompanyCheckItem]:
    """カテゴリ別に日本企業向けチェックリスト項目を取得."""
    return [c for c in JAPAN_COMPANY_CHECKLIST if c.category == category]


def get_eu_to_meti_mapping() -> dict[str, list[str]]:
    """EU AI Act チェック項目ID -> METI要件IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for item in JAPAN_COMPANY_CHECKLIST:
        if item.meti_mapping:
            mapping[item.check_id] = list(item.meti_mapping)
    return mapping


def get_eu_to_iso_mapping() -> dict[str, list[str]]:
    """EU AI Act チェック項目ID -> ISO要求事項IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for item in JAPAN_COMPANY_CHECKLIST:
        if item.iso_mapping:
            mapping[item.check_id] = list(item.iso_mapping)
    return mapping
