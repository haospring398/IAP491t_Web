"""Kiểm tra web/scripts/bundle-run.py trên run fixture: chép đúng, lỗi thì không đổi web/model/."""
import contextlib
import hashlib
import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
SCRIPT = TESTS.parents[1] / "scripts" / "bundle-run.py"
FIXTURE_RUN = TESTS / "fixture_run"
MANIFEST = "dumped_models/classification/run_manifest.json"


def load_script():
    spec = importlib.util.spec_from_file_location("bundle_run", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(folder):
    """Tên và SHA-256 của mọi file (bỏ thư mục tạm), để so trước/sau một lần chạy lỗi."""
    return {str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(folder.rglob("*")) if path.is_file()}


class BundleRun(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.temp.name)
        self.run = root / "source" / "2026-01-01_fixture"
        shutil.copytree(FIXTURE_RUN, self.run)
        self.nltk = root / "nltk_data"
        (self.nltk / "corpora" / "stopwords").mkdir(parents=True)
        (self.nltk / "corpora" / "stopwords" / "english").write_text("a\nthe\n", encoding="utf-8")
        (self.nltk / "corpora" / "wordnet.zip").write_bytes(b"wordnet placeholder")
        self.model = root / "model"
        self.script = load_script()

    def tearDown(self):
        self.temp.cleanup()

    def bundle(self):
        with patch.object(self.script, "MODEL_ROOT", self.model), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return self.script.main(["--run", str(self.run), "--nltk-data", str(self.nltk)])

    def test_good_run_copies_manifest_bytes_artifacts_and_nltk(self):
        self.assertEqual(self.bundle(), 0)
        bundled = self.model / self.run.name
        self.assertEqual((bundled / MANIFEST).read_bytes(), (self.run / MANIFEST).read_bytes())
        self.assertEqual(snapshot(bundled), snapshot(self.run))
        self.assertTrue((self.model / "nltk_data" / "corpora" / "stopwords" / "english").is_file())
        self.assertTrue((self.model / "nltk_data" / "corpora" / "wordnet.zip").is_file())
        self.assertEqual([path.name for path in self.model.iterdir() if path.name.startswith(".")], [])

    def test_bad_source_exits_non_zero_and_leaves_previous_bundle(self):
        self.assertEqual(self.bundle(), 0)
        before = snapshot(self.model)
        tampered = self.run / "data_X_test.npy"
        tampered.write_bytes(tampered.read_bytes() + b"x")
        self.assertEqual(self.bundle(), 1)
        tampered.unlink()
        self.assertEqual(self.bundle(), 1)
        self.assertEqual(snapshot(self.model), before)

    def test_missing_nltk_data_writes_nothing(self):
        shutil.rmtree(self.nltk / "corpora" / "stopwords")
        self.assertEqual(self.bundle(), 1)
        self.assertEqual(snapshot(self.model), {})


if __name__ == "__main__":
    unittest.main()
