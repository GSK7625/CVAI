# AI Evaluation Framework

This directory will hold the evaluation framework for measuring AI quality
across all features.

## Purpose

Before shipping, each AI capability must be evaluated against curated test
cases to verify quality, consistency, and accuracy.

## Future structure

```text
evaluation/
├── datasets/           ← curated test inputs and expected outputs
├── cv_analyzer/         ← evaluation scripts for CV Analyzer
├── job_matching/        ← evaluation scripts for Job Matching
├── cv_improvement/      ← evaluation scripts for CV Improvement
├── career_assistant/    ← evaluation scripts for Career Assistant
└── README.md            ← (this file)
```

## Example evaluation case (Job Matching)

```text
Input:
  Candidate A (skills: React, TypeScript, Node.js)
  Job X (required: React, TypeScript, Docker)

Expected:
  matched_skills: [React, TypeScript]
  missing_skills: [Docker]
  score_range: 60–80
```

## Status

**Not yet implemented.** Evaluation datasets and scripts will be created
during the implementation phase.
