"""python predict.py --artifact-dir runs/e5-v1/full --input example_input.json"""
import argparse
import json
import sys
from pathlib import Path

from pipeline import Reviewer
from jd_review import prepare_input, review_with_diagnostics


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sample = json.loads(args.input.read_text(encoding="utf-8"))
    # Validate and prepare before loading model resources.
    prepare_input(sample)
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    result = review_with_diagnostics(Reviewer(args.artifact_dir), sample)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
