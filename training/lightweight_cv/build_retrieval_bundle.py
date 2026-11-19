"""Build the self-contained Colab input bundle for the R1 retrieval experiment."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "datasets"


def build(context=False):
    output = ROOT / ("cvai_retrieval_r2.zip" if context else "cvai_retrieval_r1.zip")
    with ZipFile(output.with_suffix(".tmp"), "w", ZIP_DEFLATED) as archive:
        for name in ("train_retrieval_mlp.py", "evaluate_jake.py", "pipeline.py", "jd_parser.py",
                     "pdf_text.py", "requirements.txt", "THIRD_PARTY.md", "train_retrieval_r1.ipynb"):
            archive.write(ROOT / name, name)
        for name in ("train.jsonl", "validation.jsonl", "test.jsonl", "label_provenance.jsonl",
                     "DATASET_CARD.md", "manifest.json"):
            archive.write(DATA / "cvai_augmented_r1" / name, "data/" + name)
        for path in sorted((DATA / "jake_pdf_pilot").iterdir()):
            if path.suffix in (".pdf", ".json"):
                archive.write(path, "pdf/" + path.name)
        if context:
            for name in ("improve_retrieval_mlp.py", "retrieved_context.py", "evidence_features.py",
                         "jd_parser_v2.py", "jd_review.py", "predict.py", "train_retrieval_r2.ipynb"):
                archive.write(ROOT / name, name)
            for path in sorted((DATA / "jake_pdf_followup").iterdir()):
                if path.suffix in (".pdf", ".json"):
                    archive.write(path, "pdf_followup/" + path.name)
    output.with_suffix(".tmp").replace(output)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", action="store_true", help="include the R2 head and both PDF diagnostics")
    build(parser.parse_args().context)
