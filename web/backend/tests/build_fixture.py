"""Tạo lại run fixture commit sẵn trong tests/fixture_run/ (cần repository đầy đủ).

Chạy từ thư mục gốc của PhishingEmailDetection:

    .venv/Scripts/python.exe web/backend/tests/build_fixture.py

Train một run 19-10 nhỏ trên email tổng hợp bằng train.py gốc nhưng với preprocess.py và
pipeline_cache.py đóng băng (import package backend trước để đặt frozen_pipeline lên đầu
sys.path), rồi chỉ giữ run_manifest.json và các artifact có trong manifest. Test backend
không import file này; chỉ khi đổi bản đóng băng hoặc synthetic_email mới cần chạy lại.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
REPOSITORY = TESTS.parents[2]


def main():
    # Vector Doc2Vec (kể cả mảng test) phụ thuộc hash seed của Python; train với cùng
    # PYTHONHASHSEED=0 như tiến trình con của service để test so được vector lúc phục vụ.
    if os.environ.get("PYTHONHASHSEED") != "0":
        environment = {**os.environ, "PYTHONHASHSEED": "0"}
        raise SystemExit(subprocess.run([sys.executable, str(Path(__file__).resolve())], env=environment).returncode)
    sys.path.insert(0, str(TESTS))
    import test_demo  # Import package backend: frozen_pipeline đứng đầu sys.path.
    # Thư mục gốc đứng sau frozen_pipeline nên train.py dùng hai module đóng băng.
    sys.path.append(str(REPOSITORY))
    import pandas as pd
    import pipeline_cache
    import preprocess
    import train
    from dataset_audit import record_id
    rows = test_demo.fixture_rows()
    # test_demo tự tính RecordId để không import module gốc; phải trùng dataset_audit.record_id.
    mismatched = [row["Location"] for row in rows if row["RecordId"] != record_id(row["Location"])]
    if mismatched:
        raise SystemExit(f"RecordId khác dataset_audit.record_id: {mismatched[:3]}")
    frozen = test_demo.backend_module.FROZEN_PIPELINE
    for module in (preprocess, pipeline_cache):
        if Path(module.__file__).resolve().parent != frozen:
            raise SystemExit(f"{module.__name__} không phải bản đóng băng: {module.__file__}")
    frame = pd.DataFrame(rows)
    target = test_demo.FIXTURE_RUN
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        root = Path(temp)
        run = root / "run"
        # BASE_DIR tạm để cache tiền xử lý không ghi vào thư mục project.
        with patch.object(train, "BASE_DIR", root), contextlib.redirect_stdout(io.StringIO()):
            manifest = train.training(data=frame, output_dir=run, epochs=5, train_bert=False, run_ablation=False)
        staging = root / "fixture_run"
        for relative, digest in manifest["artifacts"].items():
            source = run / relative
            if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                raise SystemExit(f"Artifact không khớp manifest: {relative}")
            (staging / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, staging / relative)
        shutil.copyfile(run / test_demo.MANIFEST, staging / test_demo.MANIFEST)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(staging, target)
    print(json.dumps({"fixture": str(target), "selected_model": manifest["selected_model"],
                      "artifacts": len(manifest["artifacts"])}))


if __name__ == "__main__":
    main()
