"""Fetch a checksummed CPU artifact; never overwrite an existing installation."""
import argparse, hashlib, json, shutil, tempfile, urllib.request
from pathlib import Path
from zipfile import ZipFile
ROOT = Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=("evidence-r1", "retrieval-mlp-r2"), default="evidence-r1")
    p.add_argument("--zip", type=Path)
    p.add_argument("--destination", type=Path)
    a = p.parse_args()
    destination = a.destination or ROOT.parents[1]/"models"/a.model
    if destination.exists(): raise FileExistsError("Choose a new destination; existing model preserved")
    metadata = "retrieval_release.json" if a.model == "retrieval-mlp-r2" else "evidence_release.json"
    release = json.loads((ROOT/metadata).read_text())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cvai-install-", dir=destination.parent) as directory:
        temp = Path(directory).resolve()
        archive = a.zip or temp/"model.zip"
        if not a.zip:
            print("Downloading:", release["url"], flush=True)
            with urllib.request.urlopen(release["url"], timeout=120) as response, archive.open("wb") as out:
                shutil.copyfileobj(response, out)
        if digest(archive) != release["sha256"]: raise ValueError("Archive checksum mismatch")
        with ZipFile(archive) as z:
            names = [n for n in z.namelist() if n.startswith("artifact/")]
            if len(names) != len(set(names)) or any(".." in Path(n).parts or "\\" in n or ":" in n for n in names):
                raise ValueError("Unsafe model archive")
            if sum(z.getinfo(n).file_size for n in names) > 750_000_000: raise ValueError("Model too large")
            for name in names: z.extract(name, temp)
        artifact = temp/"artifact"
        manifest = json.loads((artifact/"manifest.json").read_text())
        if digest(artifact/"classifier.npz") != manifest["classifier_sha256"]: raise ValueError("Classifier mismatch")
        for name, expected in manifest["encoder_file_hashes"].items():
            if Path(name).name != name or digest(artifact/"encoder"/name) != expected: raise ValueError("Encoder mismatch")
        artifact.rename(destination)
    print("Installed:", destination.resolve())

if __name__ == "__main__": main()
