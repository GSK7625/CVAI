"""python predict.py --artifact-dir runs/e5-v1/full --input example_input.json"""
import argparse
import json
from pathlib import Path

from pipeline import Reviewer
from jd_parser import JDPreparationError, resolve_input


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sample = json.loads(args.input.read_text(encoding="utf-8"))
    # Parse before loading E5; an unsupported JD must not consume model resources.
    try:
        resolve_input(sample)
    except JDPreparationError as error:
        print(json.dumps({"error": str(error), "jd_profile": error.profile}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    result = Reviewer(args.artifact_dir).review(sample)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
