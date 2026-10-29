# Candidate Job Matching Evaluation Suite

Evaluation suite for Candidate Job Matching comparing **matching-v0** (heuristic baseline) and **matching-v1-experimental** (hybrid heuristic + semantic).

---

## 1. Dataset Overview

The evaluation dataset is located at:
`evaluation/matching/datasets/matching_sanity_cases.json`

Contains **25 structured test cases** across diverse evaluation categories:

| Category | Cases | Description |
| :--- | :--- | :--- |
| `exact_match` | case_01 | Candidate matches all required skills, experience, education, and domain. |
| `alias_matching` | case_02, case_03 | Resolves canonical skill aliases (ReactJS, TypeScript, NodeJS, k8s, postgres). |
| `experience_mismatch` | case_04 | Junior candidate (1 yr) applying for Senior role (5 yrs required). |
| `experience_surplus` | case_05 | Senior candidate (8 yrs) applying for Junior role (1 yr required). |
| `skill_mismatch` | case_06 | Candidate lacks all mandatory skills for the position. |
| `domain_mismatch` | case_07 | Complete cross-domain mismatch (e.g. Accountant applying for DevOps). |
| `education_mismatch` | case_08 | Candidate degree does not meet mandatory minimum (High School vs Master). |
| `education_match` | case_09 | Candidate degree meets or exceeds academic qualification requirement. |
| `project_relevance` | case_10, case_11, case_12 | Direct project technology match, zero project overlap, and zero listed projects. |
| `neutral_criteria` | case_13 | Job posting with no skills specified (neutral evaluation). |
| `skill_structure` | case_14, case_15 | Preferred skills only vs. 100% required skills with 0% preferred skills. |
| `adversarial_robustness` | case_16, case_17 | Adversarial prompt override attempts in CV summary or JD text. |
| `privacy_redaction` | case_18 | Free-text emails and phone numbers to verify deterministic redaction. |
| `domain_overlap` | case_19, case_20 | Partial domain transitions (Data Engineer -> Backend, ML -> Data Science). |
| `cross_framework` | case_21 | Cross-framework mobile transition (Flutter/Dart -> React Native). |
| `role_specialization` | case_22 | Fullstack developer applying for pure Frontend UI role. |
| `fresh_graduate` | case_23 | Recent graduate with degree, academic projects, 0 formal years experience. |
| `skill_vs_experience` | case_24, case_25 | High skills with low experience vs. 15 years experience with outdated stack. |

---

## 2. Running Evaluations

### A. Offline Deterministic Regression (Mock Provider)
Default mode for local development, CI pipelines, and automated test runners. Uses cryptographic SHA-256 token hashing:

```powershell
python -m evaluation.matching.evaluate --provider mock
```

> [!NOTE]
> **Mock Provider Disclaimer:**
> When executed with `--provider mock`, embeddings are generated via deterministic SHA-256 token hashing without network calls. Mock results serve strictly for regression testing and behavioral verification. They must **NOT** be used as evidence of improved semantic retrieval quality over `matching-v0`.

### B. Real Semantic Evaluation (OpenAI Embeddings)
Requires configured `OPENAI_API_KEY` in environment or `.env`:

```powershell
python -m evaluation.matching.evaluate --provider openai
```

---

## 3. Metrics Definitions

- **Score Mean ± StdDev**: Central tendency and dispersion of scores across the evaluation cohort.
- **Score Range [Min, Max]**: Minimum and maximum scores produced across all test cases.
- **Expected Range Compliance**: Percentage of cases whose score falls within human-annotated expected bounds.
- **Pairwise Ranking Accuracy**: Percentage of predefined precedence pairs correctly ordered (e.g. Exact Match > Junior for Senior, Relevant Projects > Unrelated Projects).
- **High-Fit vs Mismatch Delta**: Difference in average score between high-fit candidates and completely mismatched candidates.
- **PII Leakage Detected**: Count of instances where candidate's `full_name`, `email`, or `phone` leaked into semantic embedding representations (target: strictly 0).

---

## 4. Algorithm Comparison

| Dimension | `matching-v0` | `matching-v1-experimental` |
| :--- | :--- | :--- |
| **Status** | Heuristic Baseline (Default) | Experimental Hypothesis |
| **Skill Weight** | 50% | 40% |
| **Experience Weight** | 30% | 20% |
| **Education Weight** | 20% | 10% |
| **Project Relevance Weight**| Informational only (0%) | 10% (Deterministic Score) |
| **Semantic Similarity Weight**| Not used (0%) | 20% (Pure Domain Cosine Similarity) |
| **Embedding Calls** | **0 calls** | 1 batch call (Single Match) / 1 call per Job (Ranking) |
| **Calibration Status** | Engineering baseline | **UNCALIBRATED EXPERIMENTAL WEIGHTS** |

