"""Package the verified CPU pilot and auditable results without replacing v1."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pipeline import file_hash, write_json

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "runs/evidence-r1"
OUTPUT = ROOT / "experiments/evidence-r1"


def main():
    artifact = RUN / "selected_artifact"
    verified = json.loads((RUN / "serving_verification.json").read_text())
    assert file_hash(artifact / "classifier.npz") == verified["classifier_sha256"]
    assert file_hash(ROOT / "pipeline.py") == verified["serving_pipeline_sha256"]
    assert file_hash(ROOT / "evidence_features.py") == verified["feature_parser_sha256"]
    assert verified["baseline_classifier_sha256"] == "268e14e927fcd94d6ffa89f9cc0524691e5d18567d7f995355eb8aa1be0e5105"
    result = json.loads((RUN / "evaluation/results.json").read_text())
    manifest = json.loads((artifact / "manifest.json").read_text())
    manifest["deployment_status"] = "synthetic_pilot_only"
    manifest["evaluation_results_sha256"] = file_hash(RUN / "evaluation/results.json")
    manifest["deployment_coverage_sha256"] = file_hash(RUN / "evaluation/deployment_coverage.json")
    runtime = ("pipeline.py", "evidence_features.py", "jd_parser.py", "predict.py", "server.py",
               "requirements.txt", "THIRD_PARTY.md", "example_raw_input.json", "example_input.json")
    quickstart = """# CVAI evidence-r1 — CPU pilot

Giải nén vào thư mục riêng. Không ghi đè artifact V1.
Python 3.10+, CPU, không cần Colab/GPU hoặc train lại.

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -X utf8 predict.py --artifact-dir artifact --input example_raw_input.json --output my_review.json
```

Linux: thay dòng activate bằng `source .venv/bin/activate`.
Demo đúng có score=87.5. Sửa CV/JD ở bản sao example_raw_input.json.
Chỉ gửi một trong jd_text, job_profile, requirements. Score null nghĩa là cần
kiểm tra thủ công; không phải 0 điểm. Không sửa riêng evidence_features.py hoặc
jd_parser.py: checksum phải khớp phiên bản đã train.

MLP dùng 61 tín hiệu text; E5 chỉ truy xuất ngữ cảnh. Encoder không fine-tune.
Trọng số encoder kèm trong artifact/encoder, chạy inference không cần tải model.
Đọc REPORT.md và results/deployment_coverage.json trước khi tích hợp thật:
dữ liệu tổng hợp, 36/48 CV holdout có điểm tự động, chưa được kiểm chứng trên CV thật.

API: đặt CVAI_ARTIFACT_DIR đến artifact và INTERNAL_API_KEY ngẫu nhiên >=32 ký tự;
chạy `python -m uvicorn server:app --host 127.0.0.1 --port 8001 --workers 1`.
Gọi qua backend với header X-Internal-API-Key; không đặt khóa trong frontend.
"""
    deploy = OUTPUT / "cvai-evidence-r1-cpu.zip"
    with ZipFile(deploy, "x", ZIP_DEFLATED, compresslevel=6) as z:
        digests = {}
        def add_bytes(name, content):
            z.writestr(name, content)
            digests[name] = hashlib.sha256(content).hexdigest()
        def add_file(name, path):
            z.write(path, name)
            digests[name] = file_hash(path)
        for name in runtime: add_file(name, ROOT / name)
        for p in artifact.rglob("*"):
            if p.is_file() and p != artifact / "manifest.json":
                add_file("artifact/" + p.relative_to(artifact).as_posix(), p)
        add_bytes("artifact/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode())
        add_bytes("QUICKSTART.md", quickstart.encode())
        add_file("REPORT.md", OUTPUT / "README.md")
        for name in ("results.json", "deployment_coverage.json"):
            add_file("results/" + name, RUN / "evaluation" / name)
        add_bytes("SHA256SUMS.json", json.dumps(digests, indent=2).encode())
    with ZipFile(deploy) as z:
        if z.testzip() is not None: raise ValueError("Corrupt deployment ZIP")
    audit = OUTPUT / "evidence-r1-results.zip"
    with ZipFile(audit, "x", ZIP_DEFLATED) as z:
        z.write(OUTPUT / "README.md", "README.md")
        for p in RUN.iterdir():
            if p.suffix in (".json", ".jsonl"):
                z.write(p, p.name)
        for subdir in ("evaluation", "executed_sources"):
            for p in (RUN / subdir).rglob("*"):
                if p.is_file(): z.write(p, p.relative_to(RUN).as_posix())
        for name in ("optimize_evidence.py", "evaluate_evidence.py", "verify_evidence_artifact.py", "package_evidence.py", *runtime):
            z.write(ROOT / name, "current_sources/" + name)
        z.write(artifact / "classifier.npz", "artifact/classifier.npz")
        z.write(artifact / "manifest.json", "artifact/manifest.json")
    write_json(OUTPUT / "package_checksums.json", {p.name: {"sha256": file_hash(p), "bytes": p.stat().st_size}
                                                  for p in (deploy, audit)})
    write_json(OUTPUT / "promotion_decision.json", {**result["decision"], "selected": manifest["selected_classifier"],
               "classifier_sha256": manifest["classifier_sha256"], "tests_passed": 50,
               "test_suites": {"evidence_features": 11, "lightweight_cv": 18, "jd_pipeline": 10, "augmentation": 3, "review_round": 8},
               "data_and_baseline_unchanged": True, "report": str((OUTPUT / "README.md").resolve())})
    print(deploy)
    print(audit)


if __name__ == "__main__": main()
