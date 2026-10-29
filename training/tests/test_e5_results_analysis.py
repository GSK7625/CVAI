"""Uploaded archives must be unambiguous before any analysis is attempted."""
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lightweight_cv"))
from analyze_results import analyze


class ArchiveTests(unittest.TestCase):
    def test_duplicate_metrics_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("a/metrics.json", "{}")
                archive.writestr("b/metrics.json", "{}")
            with self.assertRaisesRegex(ValueError, "metrics.json"):
                analyze(path, Path(directory))

    def test_missing_predictions_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("metrics.json", "{}")
            with self.assertRaisesRegex(ValueError, "test_predictions.jsonl"):
                analyze(path, Path(directory))


if __name__ == "__main__":
    unittest.main()
