# Contract Tests

Contract tests verify that the **request/response shapes** exchanged between
the .NET Backend and the AI Service match expectations on both sides.

This is important because the two services are developed independently
(.NET vs Python) and communicate via REST.

## Purpose

```text
.NET expected request
        ↕
AI actual request/response
```

## Status

**Not yet implemented.** Contract test scaffolding will be created
during the integration phase when the .NET ↔ AI communication is connected.

## Future structure

```text
contract/
├── test_cv_analyzer_contract.py
├── test_job_matching_contract.py
├── test_cv_improvement_contract.py
├── test_career_assistant_contract.py
└── test_candidate_ranking_contract.py
```
