"""Model installation accepts only the release's exact checksummed file set."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lightweight_cv"))
from fetch_model import check_members, install


class ModelDownloadTests(unittest.TestCase):
    def test_traversal_or_extra_files_are_rejected(self):
        with self.assertRaises(ValueError):
            check_members(["artifact/encoder/../../evil.py"], ["artifact/encoder/model.safetensors"])
        with self.assertRaises(ValueError):
            check_members(["artifact/manifest.json"] * 2, ["artifact/manifest.json"])

    def test_bad_hash_is_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "wrong.zip"
            source.write_bytes(b"not the published model")
            target = Path(directory) / "encoder"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                install(source, target, {}, {"sha256": "0" * 64})
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
