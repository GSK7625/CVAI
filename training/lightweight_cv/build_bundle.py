"""Build the small Colab v1 code/data bundle, without weights or evaluation outputs."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
FILES = ("pipeline.py", "jd_parser.py", "prepare_jd.py", "predict.py", "server.py", "requirements.txt",
         "train.py", "evaluate.py", "example_input.json", "example_raw_input.json", "example_raw_jd.txt",
         "README.md", "END_TO_END.md", "THIRD_PARTY.md", "train_e5_classifier.ipynb")

if __name__ == "__main__":
    output = ROOT / "futurecv_e5_bundle.zip"
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(ROOT / name, "futurecv_e5/" + name)
        for split in ("train", "validation", "test"):
            z.write(ROOT.parent / "datasets/cvai_v1" / f"{split}.jsonl", f"futurecv_e5/data/{split}.jsonl")
    print(output)
