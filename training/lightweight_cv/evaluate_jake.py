"""Evaluate the selected artifact on PDF bytes using the project's PDF reader and reviewer."""
import argparse
import json
from pathlib import Path

from pdf_text import extract_pdf
from pipeline import Reviewer, file_hash, metrics, write_json


def evaluate(artifact, directory, output, device):
    rows = json.loads((directory / "cases.json").read_text(encoding="utf8"))["samples"]
    reviewer = Reviewer(artifact, device=device)
    predictions, cases = [], []
    found = supported = 0
    for row in rows:
        path = directory / row["pdf"]
        if file_hash(path) != row["pdf_sha256"]:
            raise ValueError(f"PDF changed: {path}")
        text = extract_pdf(path.read_bytes())
        if text != row["cv_text"]:
            raise ValueError(f"PDF extraction changed: {path}")
        review = reviewer.review(dict(sample_id=row["sample_id"], requirements=row["requirements"], cv_text=text))
        for gold, actual in zip(row["target"]["assessments"], review["assessments"], strict=True):
            assert gold["id"] == actual["id"]
            evidence = gold["evidence"]
            hit = None
            if evidence:
                span = gold["span"]
                assert text[span["start"]:span["end"]] == evidence
                hit = any(evidence in c["text"] for c in actual["retrieved_context"])
                supported += 1
                found += hit
            predictions.append(actual["status"])
            cases.append(dict(pdf=row["pdf"], requirement=actual["requirement_text"], gold=gold["status"],
                              predicted=actual["status"], gold_evidence=evidence, hit_at_3=hit,
                              retrieved=actual["retrieved_context"]))
    result = metrics(rows, predictions)
    result.update(span_recall_at_3=found / supported, gold_spans=supported, cases=cases,
                  source="synthetic Jake-layout diagnostic; structured JD requirements")
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("artifact-dir", "pdf-dir", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    evaluate(args.artifact_dir, args.pdf_dir, args.output, args.device)
