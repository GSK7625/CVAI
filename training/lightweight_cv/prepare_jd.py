"""Prepare a versioned job profile from a UTF-8 JD text file, without loading E5."""
import argparse
import json
from pathlib import Path

from jd_parser import prepare_jd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", type=Path, required=True)
    parser.add_argument("--job-title", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    result = prepare_jd(args.jd.read_text(encoding="utf-8-sig"), args.job_title)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    raise SystemExit(0 if result["status"] == "ready" else 2)
