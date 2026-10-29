"""JD preview needs neither the training cell nor an existing Python import path."""
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1] / "lightweight_cv"


def preview_source():
    notebook = json.loads((ROOT / "train_e5_classifier.ipynb").read_text(encoding="utf-8"))
    return next("".join(c["source"]) for c in notebook["cells"]
                if c["cell_type"] == "code" and "from jd_parser import prepare_jd" in "".join(c["source"]))


class PreviewTests(unittest.TestCase):
    def test_inference_cell_runs_without_training_cell_imports(self):
        notebook = json.loads((ROOT / "train_e5_classifier.ipynb").read_text(encoding="utf-8"))
        source = next("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"
                      and '"predict.py"' in "".join(c["source"]))
        fake = MagicMock()
        fake.run.return_value.stdout = '{"score":50}'
        fake.run.return_value.stderr = ""
        namespace = {"RUN_MODE": "full", "CODE_DIR": ROOT, "RUN_DIR": Path("saved-full-artifact")}
        with patch.dict(sys.modules, {"subprocess": fake}), redirect_stdout(StringIO()) as output:
            exec(source, namespace)
        self.assertIn('"score":50', output.getvalue())
        fake.run.return_value.check_returncode.assert_called_once()
        self.assertTrue(fake.run.call_args.kwargs["capture_output"])

    def test_missing_bundle_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "Không cần train lại"):
                exec(preview_source(), {"CODE_DIR": Path(directory)})

    def test_preview_imports_after_extract_without_config_or_training(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("jd_parser.py", "example_raw_input.json"):
                shutil.copy2(ROOT / name, Path(directory) / name)
            namespace = {"CODE_DIR": Path(directory)}
            with patch.dict(sys.modules), patch.object(sys, "path", list(sys.path)), redirect_stdout(StringIO()):
                sys.modules.pop("jd_parser", None)
                exec(preview_source(), namespace)
            self.assertEqual(namespace["job_profile"]["status"], "ready")
            self.assertNotIn("RUN_DIR", namespace)


if __name__ == "__main__":
    unittest.main()
