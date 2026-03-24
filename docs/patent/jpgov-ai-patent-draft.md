# United States Provisional Patent Application

## AUTOMATED AI GOVERNANCE COMPLIANCE ASSESSMENT SYSTEM WITH CRYPTOGRAPHIC AUDIT TRAIL AND CONTEXT-AWARE REMEDIATION GENERATION

---

### Filing Information

- **Applicant:** Yutaro Maeda
- **Filing Date:** [To be filled upon filing]
- **Application Type:** Provisional Patent Application under 35 U.S.C. 111(b)

---

## TITLE OF THE INVENTION

Automated AI Governance Compliance Assessment System with Dynamic Regulatory Requirement Mapping, Context-Aware Remediation Action Generation, and Cryptographically Verifiable Audit Trail

---

## ABSTRACT

A computer-implemented system and method for automating artificial intelligence (AI) governance compliance assessment. The system receives an organization's AI utilization profile—including industry classification, AI deployment patterns, data categories processed, and organizational scale—and dynamically maps applicable regulatory requirements from AI governance frameworks with context-specific weighting and prioritization. Unlike static checklist tools, the system generates an organization-specific risk profile that determines which requirements are most critical and in what order they should be addressed. A gap analysis engine identifies compliance deficiencies, and a large language model (LLM)-powered remediation engine generates concrete, context-aware improvement actions including policy document templates, technical countermeasures, and organizational measures tailored to the organization's specific context. All system operations—including assessment submissions, evidence uploads, score modifications, and report generations—are recorded in a tamper-evident audit ledger implementing a SHA-256 hash chain with Merkle Tree verification, enabling mathematical proof of audit trail integrity to regulatory authorities. The system further tracks governance maturity over time through periodic reassessment, automatically identifying the impact scope when regulatory requirements change.

---

## FIELD OF THE INVENTION

The present invention relates generally to regulatory compliance automation systems, and more particularly to a computer-implemented system and method for automating AI governance compliance assessment with cryptographically verifiable audit trails and machine learning-powered remediation action generation.

---

## BACKGROUND OF THE INVENTION

### The Problem of Manual Compliance Assessment

Organizations seeking to demonstrate compliance with AI governance frameworks—such as Japan's Ministry of Economy, Trade and Industry (METI) AI Business Operator Guidelines, the EU AI Act, and ISO/IEC 42001—face a fundamentally manual and expertise-intensive process. The current state of practice mirrors the traditional approach to Privacy Mark (JIS Q 15001) and ISMS (ISO/IEC 27001) certification:

1. **Engagement of External Consultants:** Organizations typically engage specialized consulting firms at costs ranging from USD 5,000 to USD 200,000+ depending on scope, organizational size, and certification type. For AI governance specifically, major consulting firms (PwC, EY, Deloitte, KPMG, NTTData) charge multi-million yen engagements for governance framework establishment, with total costs for comprehensive AI governance consulting commonly reaching JPY 5,000,000–30,000,000 (approximately USD 35,000–200,000).

2. **Static Checklist Approach:** Both manual consulting and existing software tools (OneTrust, Vanta, Drata, Sprinto) employ a static checklist methodology—the same set of requirements is presented to every organization regardless of their specific AI utilization patterns, risk profile, or industry context. This results in organizations spending equal effort on high-risk and low-risk requirements, leading to inefficient resource allocation.

3. **Generic Remediation Guidance:** When gaps are identified, existing tools typically provide either (a) no remediation guidance, leaving the organization to determine corrective actions independently, or (b) generic, one-size-fits-all guidance that does not account for the organization's industry, AI use cases, data types, or organizational maturity.

4. **Audit Trail Vulnerability:** Current compliance management systems store assessment history in conventional databases without cryptographic integrity verification. Assessment results, evidence records, and compliance status changes can be modified without detection, undermining the credibility of self-assessment regimes with regulatory authorities.

5. **Snapshot-Based Assessment:** Existing approaches produce point-in-time compliance snapshots without systematic tracking of governance maturity evolution over time, making it impossible to demonstrate continuous improvement or automatically assess the impact of regulatory requirement changes.

### Limitations of Existing Compliance Software

General-purpose Governance, Risk, and Compliance (GRC) platforms such as OneTrust (annual licensing starting at USD 10,000–50,000+), Vanta (USD 7,500–100,000/year), Drata (USD 7,500–100,000+/year), and Sprinto (starting from USD 4,000/year) provide workflow automation for established certification frameworks (SOC 2, ISO 27001, GDPR). However, these platforms exhibit critical limitations when applied to AI governance:

- **No AI-specific risk profiling:** They treat all organizations identically, without considering the diversity of AI deployment patterns (model training vs. API consumption vs. embedded AI), data sensitivity levels, or sector-specific AI risks.
- **No dynamic requirement weighting:** Requirements are presented as flat checklists without prioritization based on the organization's specific risk exposure.
- **No context-aware remediation generation:** Gap identification produces binary "compliant/non-compliant" flags without generating actionable, organization-specific improvement plans.
- **No cryptographic audit integrity:** Audit logs are stored in mutable databases, providing no mathematical guarantee of non-tampering.

### Need for the Invention

There exists a need for a system that: (a) dynamically maps regulatory requirements based on an organization's AI utilization profile and risk characteristics; (b) generates specific, actionable remediation plans using AI that understands the organization's context; (c) provides cryptographically verifiable audit trails that enable mathematical proof of assessment integrity; and (d) tracks governance maturity over time to demonstrate continuous improvement and assess regulatory change impact.

---

## SUMMARY OF THE INVENTION

The present invention provides an automated AI governance compliance assessment system comprising:

A **dynamic regulatory requirement mapping engine** that receives an organization profile including industry classification, AI deployment patterns (developer, provider, user), data categories processed, and organizational scale, and generates a risk-weighted, prioritized mapping of applicable regulatory requirements specific to that organization;

A **gap analysis engine** that evaluates the organization's current compliance posture against the dynamically mapped requirements, producing a multi-dimensional compliance assessment with per-requirement scoring, category-level maturity indicators, and overall governance maturity level classification;

A **context-aware remediation generation engine** powered by a large language model (LLM) that generates concrete improvement actions—including policy document templates, technical countermeasures, and organizational measures—tailored to the organization's industry, AI use cases, data types, and current maturity level;

A **cryptographic audit trail subsystem** implementing a SHA-256 hash chain with Merkle Tree verification that records all system operations in a tamper-evident ledger, enabling any party to mathematically verify the integrity of the complete audit history; and

A **temporal maturity tracking subsystem** that maintains time-series records of governance assessments, enables trend analysis, and automatically identifies the scope of impact when regulatory requirements are added, modified, or removed.

---

## DETAILED DESCRIPTION OF THE INVENTION

### System Architecture Overview

The system comprises five principal subsystems operating in an integrated pipeline: (1) Organization Profiling and Requirement Mapping, (2) Assessment and Gap Analysis, (3) AI-Powered Remediation Generation, (4) Cryptographic Audit Trail, and (5) Temporal Maturity Tracking. Each subsystem is described in detail below.

### 1. Organization Profiling and Dynamic Requirement Mapping

#### 1.1 Organization Profile Ingestion

Upon onboarding, the system collects an organization profile comprising:

- **Industry classification** (e.g., financial services, healthcare, manufacturing, retail, technology)
- **Organizational scale** (small, medium, large, enterprise—determined by employee count, revenue, and number of AI systems deployed)
- **AI role classification** (developer: trains/fine-tunes models; provider: deploys AI services; user: consumes AI services)
- **AI utilization patterns** (enumeration of specific AI use cases, input data types, output decision types, and human oversight levels)
- **Data sensitivity profile** (categories of personal data processed, special categories under applicable privacy law, cross-border data flows)

#### 1.2 Dynamic Requirement Weighting Algorithm

Unlike static checklist approaches, the system implements a dynamic weighting algorithm that adjusts the priority and criticality of each regulatory requirement based on the organization profile:

```
For each requirement R_i in the regulatory framework:
  weight(R_i) = base_weight(R_i)
                × industry_risk_factor(R_i, organization.industry)
                × ai_role_factor(R_i, organization.ai_role)
                × data_sensitivity_factor(R_i, organization.data_profile)
                × scale_factor(R_i, organization.scale)
```

Where:
- `base_weight(R_i)` is the inherent importance of the requirement within the framework
- `industry_risk_factor` adjusts weight based on industry-specific AI risks (e.g., safety requirements weighted higher for healthcare/autonomous vehicles)
- `ai_role_factor` adjusts based on whether the organization develops, provides, or merely uses AI (e.g., data quality requirements weighted higher for developers)
- `data_sensitivity_factor` adjusts based on the sensitivity of data processed (e.g., privacy requirements weighted higher when processing biometric or health data)
- `scale_factor` adjusts for organizational complexity (e.g., governance structure requirements weighted higher for large organizations)

The output is an **Organization-Specific Requirement Map (OSRM)** containing all applicable requirements ranked by weighted priority, grouped by governance domain (safety, fairness, privacy, security, transparency, accountability, education, competition, innovation).

#### 1.3 Risk Profile Generation

The system generates a composite risk profile for the organization:

- **Risk Heat Map:** A matrix visualization showing requirement domains (rows) against risk severity (columns), with each cell's color intensity determined by the dynamic weight calculation
- **Critical Requirement Set:** The subset of requirements exceeding a configurable criticality threshold, which must be addressed as highest priority
- **Recommended Assessment Sequence:** An optimized ordering for self-assessment that addresses highest-risk areas first

### 2. Assessment and Gap Analysis Engine

#### 2.1 Adaptive Questionnaire

The system presents a self-assessment questionnaire whose content and depth adapt based on the OSRM:

- Questions are drawn from a comprehensive question bank covering all requirements in the applicable regulatory framework
- Question ordering reflects the priority ranking from the OSRM
- Each question maps to one or more specific regulatory requirements via a many-to-many relationship
- Response options follow a Likert-scale pattern (e.g., 5-level: "Not implemented" through "Fully implemented with continuous improvement")

In the reference implementation, the system covers Japan's METI AI Business Operator Guidelines v1.1, with 10 governance domains (C01: Human-Centric through C10: Innovation), each containing 2-4 specific requirements (total: 26 requirements), assessed through domain-specific questions.

#### 2.2 Scoring Algorithm

For each requirement R_i, the system computes:

- **Requirement Score:** Average of scores from all questions mapping to R_i, normalized to a 0.0–4.0 scale
- **Compliance Status Determination:**
  - Score >= 3.0 → COMPLIANT
  - 1.5 <= Score < 3.0 → PARTIAL
  - Score < 1.5 → NON_COMPLIANT
- **Category Score:** Weighted average of requirement scores within each governance domain
- **Overall Maturity Level:** Mapped from overall score to a 5-level maturity model:
  - Level 1 (Initial): Ad hoc, reactive
  - Level 2 (Repeatable): Basic processes established
  - Level 3 (Defined): Standardized processes
  - Level 4 (Managed): Quantitatively managed
  - Level 5 (Optimizing): Continuous improvement

#### 2.3 Gap Identification

For each requirement with status PARTIAL or NON_COMPLIANT, the gap analysis engine produces:

- **Gap Description:** A natural language description of the compliance deficiency
- **Priority Classification:** High/Medium/Low based on: (a) the compliance status, (b) the dynamic weight from the OSRM, and (c) domain criticality (safety, security, and privacy domains receive automatic priority elevation)
- **Current Score and Target Score:** Quantifying the size of the gap

### 3. Context-Aware Remediation Generation Engine

#### 3.1 LLM-Powered Remediation

This subsystem distinguishes the invention from all known prior art. Upon completion of gap analysis, the system invokes a large language model to generate remediation actions that are specifically tailored to the organization's context:

**Input to LLM:**
- The complete gap analysis result (requirement IDs, titles, compliance statuses, scores)
- The organization profile (industry, AI role, data types, scale)
- The OSRM priority ranking

**Output from LLM:**
- **Prioritized Improvement Actions:** Ranked list of specific actions, each including:
  - Action description with organization-specific details
  - Implementation steps
  - Estimated timeline and resource requirements
- **Policy Document Templates:** Pre-drafted policy language customized to the organization's industry and AI usage patterns
- **Technical Countermeasures:** Specific technical implementations recommended for the organization's technology stack and AI deployment architecture
- **Organizational Measures:** Governance structure recommendations, training program outlines, and process definitions appropriate to the organization's scale

#### 3.2 Fallback Remediation

When the LLM service is unavailable, the system provides deterministic, rule-based remediation actions from a curated action map that associates each requirement ID with a set of standard improvement actions. The fallback system also generates a phased improvement roadmap:
- Phase 1 (1-3 months): High-risk requirements (safety, security, privacy)
- Phase 2 (3-6 months): Governance structure and accountability
- Phase 3 (6-12 months): Full compliance and continuous improvement framework

### 4. Cryptographic Audit Trail Subsystem

#### 4.1 Hash Chain Architecture

The audit trail subsystem implements a cryptographic hash chain that provides mathematical guarantees of audit log integrity:

**Event Structure:**
Each audit event contains:
- `event_id`: Unique identifier (UUID-based)
- `sequence`: Monotonically increasing integer establishing total ordering
- `timestamp`: ISO 8601 UTC timestamp
- `action`: Operation type (e.g., "assessment_submitted", "evidence_uploaded", "score_modified")
- `actor`: Identity of the user or system component performing the action
- `resource_type` and `resource_id`: The target of the operation
- `details`: Structured metadata specific to the action type
- `payload_hash`: SHA-256 hash of the event's payload (action, actor, resource_type, resource_id, details), computed as SHA-256 of the canonical JSON serialization
- `previous_hash`: The `event_hash` of the immediately preceding event in the chain (or a genesis hash for the first event)
- `event_hash`: SHA-256 hash of the canonical JSON serialization of (event_id, sequence, timestamp, payload_hash, previous_hash)

**Chain Integrity:**
The chain is initialized with a genesis hash: SHA-256("JPGOV-AI-GENESIS"). Each subsequent event's `previous_hash` field points to the `event_hash` of its predecessor, creating an immutable backward-linked chain. Any modification to any event in the chain—including its payload, timestamp, or sequence number—will produce a different hash, breaking the chain at that point and all subsequent events.

#### 4.2 Merkle Tree Verification

In addition to the sequential hash chain, the system maintains a Merkle Tree over all event hashes:

- Leaf nodes: The `event_hash` values of individual audit events
- Internal nodes: SHA-256 of the concatenation of child node hashes
- Root hash: A single hash value that summarizes the integrity of the entire audit history

The Merkle Tree enables:
- **O(log n) membership proofs:** Proving that a specific event is part of the audit history without revealing other events
- **Efficient incremental updates:** Adding a new event requires recomputing only O(log n) nodes
- **Root hash publication:** The Merkle root can be periodically published to an external timestamping service or blockchain, creating an irrefutable timestamp anchor

#### 4.3 Verification Protocol

The system provides a verification function that:
1. Validates the genesis hash of the first event
2. For each event, recomputes the `event_hash` from its constituent fields and verifies it matches the stored hash
3. For each event, recomputes the `payload_hash` and verifies it matches the stored value
4. For each event (after the first), verifies that `previous_hash` matches the `event_hash` of the preceding event
5. Returns a boolean validity result and a list of any detected integrity violations

This verification can be performed by any party with read access to the audit log, including regulatory authorities, enabling independent verification of assessment integrity without trusting the system operator.

### 5. Temporal Maturity Tracking Subsystem

#### 5.1 Time-Series Assessment Records

The system maintains a complete history of all assessments for each organization, enabling:

- **Maturity Trend Analysis:** Visualization of governance maturity level changes over time, at both overall and per-domain granularity
- **Improvement Velocity Measurement:** Rate of compliance improvement across assessment cycles
- **Regression Detection:** Automatic alerting when compliance scores decrease between assessments

#### 5.2 Regulatory Change Impact Analysis

When regulatory requirements are updated (e.g., new version of METI guidelines, EU AI Act amendments):

- The system maps new/modified/removed requirements against existing assessments
- Automatically identifies which organizations are affected and in which governance domains
- Generates a delta report showing: (a) new requirements not previously assessed, (b) modified requirements requiring reassessment, (c) removed requirements that may free resources
- Recalculates compliance status under the updated framework without requiring full reassessment

### 6. Report Generation Subsystem

The system generates comprehensive compliance reports integrating all subsystem outputs:

- Organization profile and risk classification
- Assessment results with per-requirement and per-domain scoring
- Gap analysis with prioritized remediation actions
- Evidence coverage summary
- Audit trail integrity verification result (including Merkle root hash)
- Historical maturity trend (when multiple assessments exist)

Reports are generated in formats suitable for: (a) internal governance review, (b) regulatory authority submission, and (c) third-party auditor review.

---

## CLAIMS

### Independent Claim 1 — System

**1.** A computer-implemented system for automated artificial intelligence governance compliance assessment, the system comprising:

one or more processors; and

one or more non-transitory computer-readable storage media storing instructions that, when executed by the one or more processors, cause the system to:

**(a)** receive an organization profile comprising at least an industry classification, an AI role classification selected from the group consisting of developer, provider, and user, and a data sensitivity profile characterizing categories of data processed by AI systems of the organization;

**(b)** dynamically generate an organization-specific requirement map by applying a weighting algorithm to a set of regulatory requirements from an AI governance framework, wherein the weighting algorithm computes, for each regulatory requirement, a composite weight based on at least the industry classification, the AI role classification, and the data sensitivity profile of the organization, and wherein the organization-specific requirement map comprises the regulatory requirements ranked by the computed composite weights;

**(c)** present an adaptive assessment interface comprising questions mapped to the regulatory requirements, wherein the questions are ordered based on the ranking in the organization-specific requirement map;

**(d)** receive assessment responses and compute, for each regulatory requirement, a compliance score based on scores from questions mapped to that requirement, and determine a compliance status for each requirement based on the computed compliance score;

**(e)** for each regulatory requirement having a compliance status of non-compliant or partially compliant, generate context-aware remediation actions by providing the compliance scores, the organization profile, and the organization-specific requirement map to a large language model, wherein the large language model generates remediation actions comprising at least one of: policy document content tailored to the organization's industry, technical countermeasures specific to the organization's AI deployment architecture, and organizational measures appropriate to the organization's scale;

**(f)** record each operation performed by the system in a tamper-evident audit ledger, wherein each audit event in the ledger comprises a payload hash computed as a cryptographic hash of the event's payload, a previous hash field containing the event hash of the immediately preceding event in the ledger, and an event hash computed as a cryptographic hash of the event's metadata including the payload hash and the previous hash, thereby forming a hash chain; and

**(g)** maintain a Merkle Tree data structure over the event hashes of the audit events in the ledger, wherein the Merkle Tree enables O(log n) verification of individual event membership in the audit history and provides a root hash summarizing the integrity of the complete audit history.

### Dependent Claims on Claim 1

**2.** The system of claim 1, wherein the weighting algorithm further comprises:

computing an industry risk factor based on a mapping between the organization's industry classification and risk characteristics specific to each regulatory requirement domain;

computing an AI role factor based on the organization's AI role classification, wherein developer organizations receive elevated weighting for data quality and model validation requirements, provider organizations receive elevated weighting for service reliability and user notification requirements, and user organizations receive elevated weighting for appropriate use and human oversight requirements; and

computing a data sensitivity factor based on the categories of data in the data sensitivity profile, wherein requirements related to privacy and data protection receive elevated weighting when the data sensitivity profile indicates processing of biometric data, health data, or data of minors.

**3.** The system of claim 1, wherein the instructions further cause the system to:

maintain a time-series record of assessment results for each organization;

compute governance maturity trend metrics based on the time-series record; and

upon detection of a regulatory requirement change in the AI governance framework, automatically identify affected organizations and generate a delta report indicating new requirements requiring assessment, modified requirements requiring reassessment, and removed requirements.

**4.** The system of claim 1, wherein the compliance score computation further comprises:

mapping each assessment question to one or more regulatory requirements via a many-to-many relationship;

computing a requirement score as a normalized average of scores from all questions mapped to that requirement;

computing a category score as a weighted average of requirement scores within each governance domain; and

determining an overall maturity level by mapping an aggregate score to a multi-level maturity model comprising at least five levels ranging from an initial ad hoc level to an optimizing continuous improvement level.

**5.** The system of claim 1, wherein the tamper-evident audit ledger is initialized with a genesis hash computed as a cryptographic hash of a predetermined genesis string, and wherein the system further comprises a verification function that:

validates that the first event's previous hash field matches the genesis hash;

for each event, recomputes the event hash from the event's constituent fields and verifies the recomputed hash matches the stored event hash;

for each event, recomputes the payload hash and verifies the recomputed hash matches the stored payload hash;

for each event after the first, verifies that the previous hash field matches the event hash of the preceding event; and

returns a verification result indicating whether the complete audit chain is intact together with a list of any detected integrity violations.

**6.** The system of claim 1, wherein the context-aware remediation actions further comprise a fallback remediation mode that, when the large language model is unavailable, generates deterministic remediation actions from a curated action map associating each requirement identifier with a set of standard improvement actions, and generates a phased improvement roadmap organized into at least three temporal phases prioritizing safety, security, and privacy requirements in an earliest phase.

**7.** The system of claim 1, wherein the system further stores evidence records associated with specific regulatory requirements, each evidence record comprising a file reference, a description, and a file type classification, and wherein the system computes an evidence coverage metric indicating the proportion of regulatory requirements for which at least one evidence record has been uploaded.

### Independent Claim 2 — Method

**8.** A computer-implemented method for automated artificial intelligence governance compliance assessment, the method comprising:

**(a)** receiving, by one or more processors, an organization profile characterizing an organization's AI utilization, the organization profile comprising at least an industry classification, an organizational scale indicator, an AI role classification, and a data sensitivity profile;

**(b)** generating, by the one or more processors, a risk profile for the organization by applying a dynamic weighting algorithm to each requirement in an AI governance regulatory framework, wherein the dynamic weighting algorithm computes a composite weight for each requirement as a function of the organization's industry classification, AI role classification, data sensitivity profile, and organizational scale;

**(c)** generating an organization-specific requirement map comprising the requirements of the AI governance regulatory framework ranked by their computed composite weights;

**(d)** administering an adaptive self-assessment questionnaire ordered based on the organization-specific requirement map, and receiving assessment responses;

**(e)** computing compliance scores for each requirement based on the assessment responses, and determining a compliance status for each requirement, wherein the compliance status is one of compliant, partially compliant, or non-compliant based on configurable score thresholds;

**(f)** performing gap analysis by identifying requirements with a compliance status of partially compliant or non-compliant, and for each identified requirement, determining a priority classification based on the compliance status and the composite weight from the organization-specific requirement map;

**(g)** generating context-aware remediation actions by providing the gap analysis results and the organization profile to a large language model, the remediation actions comprising prioritized improvement actions with organization-specific implementation guidance;

**(h)** recording each of the receiving, generating, administering, computing, performing, and generating steps in a tamper-evident audit ledger by, for each recorded operation: computing a payload hash as a SHA-256 cryptographic hash of the operation's payload, setting a previous hash field to the event hash of the immediately preceding record in the ledger, and computing an event hash as a SHA-256 cryptographic hash of the record's metadata including the payload hash and the previous hash;

**(i)** maintaining a Merkle Tree over the event hashes, the Merkle Tree providing a root hash that changes whenever any event in the ledger is added or modified; and

**(j)** generating a compliance report integrating the organization profile, the assessment results, the gap analysis with remediation actions, and a verification result of the audit ledger integrity based on the hash chain and the Merkle Tree.

### Dependent Claims on Claim 8

**9.** The method of claim 8, further comprising:

storing the compliance report with a timestamp;

upon a subsequent assessment of the same organization, comparing the subsequent assessment results with prior assessment results to compute governance maturity trend metrics; and

generating a maturity trend visualization showing per-domain compliance score changes over time.

**10.** The method of claim 8, wherein step (g) further comprises:

constructing a prompt for the large language model that includes the gap analysis results limited to requirements with non-compliant or partially compliant status, the prompt instructing the large language model to generate prioritized improvement actions with specific implementation steps, estimated timelines, and resource requirements; and

when the large language model is unavailable, generating fallback remediation actions from a predetermined action map associating each requirement identifier with standard improvement actions.

**11.** The method of claim 8, further comprising:

receiving evidence documents associated with specific regulatory requirements;

computing an evidence coverage rate as the proportion of requirements having at least one associated evidence document;

recording each evidence upload operation in the tamper-evident audit ledger; and

including the evidence coverage rate in the compliance report.

**12.** The method of claim 8, wherein the dynamic weighting algorithm of step (b) further comprises:

for requirements in a safety domain, applying a multiplier based on the organization's AI deployment in safety-critical applications;

for requirements in a privacy domain, applying a multiplier based on the volume and sensitivity of personal data in the organization's data sensitivity profile;

for requirements in a security domain, applying a multiplier based on the organization's AI systems' network exposure and access patterns; and

for requirements in a transparency domain, applying a multiplier based on whether the organization's AI systems make decisions affecting individuals' rights or interests.

### Independent Claim 3 — Computer-Readable Medium

**13.** A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause the one or more processors to perform operations comprising:

**(a)** receiving an organization profile comprising an industry classification, an AI role classification, an organizational scale indicator, and a data sensitivity profile characterizing categories of data processed by AI systems of an organization;

**(b)** generating an organization-specific requirement map by computing, for each regulatory requirement in an AI governance framework, a composite weight based on the organization profile, and ranking the requirements by the computed composite weights;

**(c)** administering an assessment based on the organization-specific requirement map and computing compliance scores for each requirement;

**(d)** identifying compliance gaps and generating context-aware remediation actions by providing the compliance gaps and the organization profile to a large language model;

**(e)** recording all operations in a tamper-evident audit ledger implementing a SHA-256 hash chain, wherein each record's event hash is computed from its payload hash and the event hash of the preceding record; and

**(f)** maintaining a Merkle Tree over the event hashes, enabling O(log n) membership verification and providing a root hash for audit trail integrity verification.

### Dependent Claims on Claim 13

**14.** The non-transitory computer-readable medium of claim 13, wherein the operations further comprise:

maintaining a time-series database of assessment results;

upon receiving a notification of a change to the AI governance framework, automatically mapping changed requirements against existing assessment records to identify affected organizations;

generating a regulatory change impact report for each affected organization indicating requirements requiring new assessment, requirements requiring reassessment, and requirements no longer applicable; and

computing an estimated compliance status under the changed framework based on existing assessment data without requiring full reassessment.

**15.** The non-transitory computer-readable medium of claim 13, wherein generating context-aware remediation actions comprises:

selecting a subset of compliance gaps having a compliance status of non-compliant or partially compliant;

constructing a structured input for the large language model comprising the selected gaps and the organization profile;

receiving from the large language model a set of prioritized remediation actions, each action comprising an action description, implementation steps, an estimated timeline, and estimated resource requirements; and

when the large language model is unavailable, generating deterministic remediation actions from a rule-based action map and generating a phased improvement roadmap prioritizing safety, security, and privacy requirements.

---

## FIGURES (Text Descriptions)

### Figure 1: System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    JPGovAI System Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Organization │───>│  Dynamic     │───>│  Organization-   │   │
│  │ Profile      │    │  Requirement │    │  Specific        │   │
│  │ Ingestion    │    │  Mapping     │    │  Requirement Map │   │
│  └──────────────┘    │  Engine      │    │  (OSRM)          │   │
│                      └──────────────┘    └────────┬─────────┘   │
│                                                    │             │
│                                                    ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Assessment   │<───│  Adaptive    │<───│  Question Bank   │   │
│  │ Responses    │    │  Questionnaire│    │  (per framework) │   │
│  └──────┬───────┘    └──────────────┘    └──────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Scoring &    │───>│  Gap         │───>│  LLM-Powered     │   │
│  │ Compliance   │    │  Analysis    │    │  Remediation     │   │
│  │ Engine       │    │  Engine      │    │  Generation      │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         │                    │                     │             │
│         ▼                    ▼                     ▼             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Report Generation Engine                    │    │
│  └─────────────────────────────┬───────────────────────────┘    │
│                                 │                                │
│  ┌──────────────────────────────┴──────────────────────────┐    │
│  │           Cryptographic Audit Trail Subsystem            │    │
│  │  ┌─────────┐  ┌───────────────┐  ┌─────────────────┐   │    │
│  │  │ SHA-256 │  │ Hash Chain    │  │ Merkle Tree     │   │    │
│  │  │ Hashing │──│ (backward-    │──│ Verification    │   │    │
│  │  │         │  │  linked)      │  │                 │   │    │
│  │  └─────────┘  └───────────────┘  └─────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Temporal Maturity Tracking Subsystem            │    │
│  │  ┌───────────┐  ┌──────────────┐  ┌────────────────┐   │    │
│  │  │ Time-     │  │ Trend        │  │ Regulatory     │   │    │
│  │  │ Series DB │──│ Analysis     │──│ Change Impact  │   │    │
│  │  │           │  │              │  │ Detection      │   │    │
│  │  └───────────┘  └──────────────┘  └────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Figure 2: Hash Chain and Merkle Tree Structure

```
Hash Chain (Sequential Integrity):

  Genesis Hash ◄── Event 0 ◄── Event 1 ◄── Event 2 ◄── Event N
  SHA256(         prev_hash:   prev_hash:   prev_hash:   prev_hash:
  "JPGOV-AI-     genesis      event_0      event_1      event_{N-1}
   GENESIS")     event_hash:  event_hash:  event_hash:  event_hash:
                 H(meta_0)    H(meta_1)    H(meta_2)    H(meta_N)

Merkle Tree (Logarithmic Verification):

                    ┌──────────┐
                    │  Root    │
                    │  Hash    │
                    └────┬─────┘
                   ┌─────┴─────┐
              ┌────┴───┐  ┌────┴───┐
              │ H(0,1) │  │ H(2,3) │
              └───┬────┘  └───┬────┘
             ┌────┴──┐   ┌────┴──┐
           ┌─┴─┐  ┌─┴─┐ ┌─┴─┐ ┌─┴─┐
           │E_0│  │E_1│ │E_2│ │E_3│  ← Event Hashes (leaves)
           └───┘  └───┘ └───┘ └───┘
```

### Figure 3: Dynamic Requirement Weighting Process

```
Organization Profile Input:
┌──────────────────────────────────────┐
│ Industry:     Healthcare             │
│ AI Role:      Provider               │
│ Data Types:   Patient records,       │
│               Medical imaging        │
│ Scale:        Large (500+ employees) │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Dynamic Weighting Engine             │
│                                      │
│ For each Requirement R_i:            │
│   w = base × industry × role         │
│       × data_sensitivity × scale     │
│                                      │
│ Example: Safety Requirement          │
│   base=1.0 × healthcare=1.8          │
│   × provider=1.3 × medical=1.5      │
│   × large=1.1                        │
│   = 3.861 (HIGH PRIORITY)            │
│                                      │
│ Example: Innovation Requirement      │
│   base=1.0 × healthcare=1.0          │
│   × provider=1.0 × medical=1.0      │
│   × large=1.0                        │
│   = 1.000 (STANDARD PRIORITY)        │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Organization-Specific Requirement    │
│ Map (OSRM)                           │
│                                      │
│ Priority │ Req ID  │ Domain          │
│ ─────────┼─────────┼──────────       │
│ 1 (3.86) │ C02-R03 │ Safety          │
│ 2 (3.51) │ C04-R02 │ Privacy         │
│ 3 (3.22) │ C05-R01 │ Security        │
│ ...      │ ...     │ ...             │
│ 26(1.00) │ C10-R02 │ Innovation      │
└──────────────────────────────────────┘
```

### Figure 4: Context-Aware Remediation Generation Flow

```
┌───────────────┐     ┌───────────────┐     ┌──────────────┐
│ Gap Analysis  │     │ Organization  │     │ OSRM         │
│ Results       │     │ Profile       │     │ Priorities   │
│               │     │               │     │              │
│ • C02-R01: ✗  │     │ • Healthcare  │     │ • Safety: ↑↑ │
│ • C04-R02: △  │     │ • Provider    │     │ • Privacy: ↑ │
│ • C05-R01: ✗  │     │ • Patient data│     │ • Security:↑ │
└───────┬───────┘     └───────┬───────┘     └──────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │   LLM Remediation       │
                │   Engine                │
                │                         │
                │  "Given a healthcare    │
                │   AI provider handling  │
                │   patient records..."   │
                └────────────┬────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │ Context-Aware Remediation Actions       │
        │                                         │
        │ 1. AI Risk Assessment Framework         │
        │    → Medical AI safety standards         │
        │    → Patient outcome monitoring          │
        │    Timeline: 2 months                    │
        │                                         │
        │ 2. Privacy Impact Assessment             │
        │    → Patient data PIA template           │
        │    → HIPAA/APPI cross-reference          │
        │    Timeline: 1 month                     │
        │                                         │
        │ 3. Security Hardening                    │
        │    → Medical data encryption standards   │
        │    → Adversarial attack protection        │
        │    Timeline: 3 months                    │
        └────────────────────────────────────────┘
```

### Figure 5: Temporal Maturity Tracking

```
Maturity Level
     5 │                                          ●───
       │                                     ●────
     4 │                                ●────
       │                           ●────
     3 │                      ●────
       │                 ●────
     2 │            ●────
       │       ●────
     1 │  ●────
       │
       └──┬──────┬──────┬──────┬──────┬──────┬──── Time
        Q1'26  Q2'26  Q3'26  Q4'26  Q1'27  Q2'27

        ▲                              ▲
        │                              │
   Initial Assessment         Regulatory Change
   (Baseline)                 Impact Detected:
                              "2 new requirements
                               added → reassess
                               C02, C04 domains"
```

---

## INVENTOR DECLARATION

I, Yutaro Maeda, declare that I am the sole inventor of the subject matter described and claimed herein.

---

*End of Provisional Patent Application*
