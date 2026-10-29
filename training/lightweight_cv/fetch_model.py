"""Install the exact v1 encoder from a checksummed GitHub Release archive."""
import argparse
import json
import shutil
import tempfile
import urllib.request
from pathlib import Path
from zipfile import ZipFile

from pipeline import file_hash

ROOT = Path(__file__).resolve().parent


def check_members(names, allowed):
    if len(names) != len(set(names)) or set(names) != set(allowed):
        raise ValueError("Model ZIP contains missing, duplicate or unexpected files")
    if any(".." in Path(name).parts or "\\" in name or ":" in name for name in names):
        raise ValueError("Invalid archive path")


def verify_encoder(path, manifest):
    for name, expected in manifest["encoder_file_hashes"].items():
        if Path(name).name != name or file_hash(path / name) != expected:
            raise ValueError("Encoder checksum mismatch: " + name)


def install(archive, destination, manifest, release):
    if file_hash(archive) != release["sha256"]:
        raise ValueError("Release ZIP SHA-256 mismatch")
    allowed = {"artifact/classifier.npz", "artifact/manifest.json", "artifact/THIRD_PARTY.md"}
    allowed.update("artifact/encoder/" + name for name in manifest["encoder_file_hashes"])
    with tempfile.TemporaryDirectory(prefix="cvai-verified-model-") as temporary:
        staging = Path(temporary)
        with ZipFile(archive) as z:
            check_members(z.namelist(), allowed)
            if sum(info.file_size for info in z.infolist()) > 750_000_000:
                raise ValueError("Unexpected uncompressed model size")
            z.extractall(staging)
        unpacked = staging / "artifact"
        if json.loads((unpacked / "manifest.json").read_text(encoding="utf-8")) != manifest:
            raise ValueError("Release and committed manifest differ")
        if file_hash(unpacked / "classifier.npz") != manifest["classifier_sha256"]:
            raise ValueError("Classifier checksum mismatch")
        verify_encoder(unpacked / "encoder", manifest)
        if destination.exists():
            verify_encoder(destination, manifest)
        else:
            shutil.copytree(unpacked / "encoder", destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, help="Use an already downloaded model ZIP")
    args = parser.parse_args()
    artifact = ROOT / "artifact"
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    release = json.loads((ROOT / "model_release.json").read_text(encoding="utf-8"))
    if manifest["feature_version"] != "e5-top3-classifier-v1" or manifest["mode"] != "full":
        raise ValueError("Only the released full v1 artifact is supported")
    if file_hash(artifact / "classifier.npz") != manifest["classifier_sha256"]:
        raise ValueError("Committed classifier checksum mismatch")
    if args.zip:
        install(args.zip, artifact / "encoder", manifest, release)
    elif (artifact / "encoder").exists():
        verify_encoder(artifact / "encoder", manifest)
    else:
        with tempfile.TemporaryDirectory(prefix="cvai-model-download-") as temporary:
            archive = Path(temporary) / release["asset"]
            request = urllib.request.Request(release["url"], headers={"User-Agent": "CVAI-v1-model-fetcher"})
            print("Downloading:", release["url"], flush=True)
            with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as stream:
                shutil.copyfileobj(response, stream, length=1024 * 1024)
            install(archive, artifact / "encoder", manifest, release)
    print("Verified v1 artifact:", artifact)


if __name__ == "__main__":
    main()
