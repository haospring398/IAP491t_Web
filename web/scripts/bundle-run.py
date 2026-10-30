"""Đóng gói một run đã train vào web/model/ để web/ chạy được khi chép riêng.

Chỉ dùng thư viện chuẩn, chạy bằng Python nào cũng được:

    python web/scripts/bundle-run.py --run runs/2026-10-23_web2

Chép run_manifest.json, mọi artifact trong manifest (kiểm SHA-256 ngay lúc chép) và dữ
liệu NLTK đã dùng lúc train (corpora/stopwords, corpora/wordnet.zip) vào
web/model/<run-id>/ và web/model/nltk_data/. Mọi thứ được ghi vào một thư mục tạm trong
web/model/ rồi mới đổi tên vào chỗ, nên lỗi lúc chép (hash sai, thiếu file) không làm đổi
web/model/. Thư mục run và nltk_data được thay bằng hai lần đổi tên riêng; nếu lần thứ hai
lỗi sau khi thư mục run đã được thay thì thông báo lỗi nêu rõ thư mục nào đã bị thay.
--run và --nltk-data tương đối tính từ thư mục hiện hành.
"""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = WEB_ROOT.parent
MODEL_ROOT = WEB_ROOT / "model"
# Cùng vị trí manifest mà web/backend/adapter.py đọc.
MANIFEST = "dumped_models/classification/run_manifest.json"
NLTK_ITEMS = ("corpora/stopwords", "corpora/wordnet.zip")


class BundleError(Exception):
    pass


def copy_verified(source, target, expected):
    """Chép từng khối và băm đúng các byte đã chép; sai hash thì báo lỗi."""
    digest = hashlib.sha256()
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(source, "rb") as reader, open(target, "wb") as writer:
        for block in iter(lambda: reader.read(1024 * 1024), b""):
            digest.update(block)
            writer.write(block)
    if digest.hexdigest() != expected:
        raise BundleError(f"Hash không khớp manifest: {source}")


def stage_run(run, staging):
    manifest_path = run / MANIFEST
    if not manifest_path.is_file():
        raise BundleError(f"Không có manifest: {manifest_path}")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("status") != "complete" or manifest.get("schema_version") != 2:
        raise BundleError("Run chưa hoàn tất hoặc không phải schema 2")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise BundleError("Manifest không có danh sách artifact")
    destination = staging / run.name
    for relative, digest in artifacts.items():
        # Run train trên Windows có thể ghi khoá bằng "\\"; adapter cũng chuẩn hoá như vậy.
        relative = relative.replace("\\", "/")
        source = (run / relative).resolve()
        if run not in source.parents:
            raise BundleError(f"Artifact nằm ngoài run: {relative}")
        if not source.is_file():
            raise BundleError(f"Thiếu artifact: {relative}")
        copy_verified(source, destination / relative, digest)
    # Ghi đúng các byte manifest đã đọc; adapter dùng SHA-256 của chúng làm định danh release.
    (destination / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (destination / MANIFEST).write_bytes(manifest_bytes)
    if (run / MANIFEST).read_bytes() != manifest_bytes:
        raise BundleError("Manifest thay đổi trong lúc chép")
    return manifest_bytes


def stage_nltk(nltk_data, staging):
    for item in NLTK_ITEMS:
        source = nltk_data / item
        target = staging / "nltk_data" / item
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        else:
            raise BundleError(f"Thiếu dữ liệu NLTK: {source}")


def replace(staged, final):
    """Đổi tên bản mới vào chỗ; bản cũ (nếu có) được đổi tên ra trước rồi mới xoá."""
    previous = None
    if final.exists():
        previous = final.with_name(f".old-{final.name}-{uuid.uuid4().hex}")
        final.rename(previous)
    try:
        staged.rename(final)
    except OSError:
        if previous is not None:
            previous.rename(final)
        raise
    if previous is not None:
        shutil.rmtree(previous, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chép một run đã kiểm hash vào web/model/")
    parser.add_argument("--run", type=Path, required=True, help="Thư mục run, ví dụ runs/2026-10-23_web2")
    parser.add_argument("--nltk-data", type=Path, default=REPOSITORY / ".venv" / "nltk_data",
                        help="Thư mục NLTK đã dùng lúc train (mặc định <repo>/.venv/nltk_data)")
    args = parser.parse_args(argv)
    # Console Windows có thể không mã hoá được tiếng Việt; không để việc in làm hỏng lệnh.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    run = args.run.resolve()
    if not run.is_dir():
        print(f"Không tìm thấy run: {run}", file=sys.stderr)
        return 1
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    if run.name == "nltk_data" or run.name.startswith("."):
        print(f"Tên run không dùng được: {run.name}", file=sys.stderr)
        return 1
    staging = Path(tempfile.mkdtemp(prefix=".bundle-", dir=MODEL_ROOT))
    replaced = []
    try:
        manifest_bytes = stage_run(run, staging)
        stage_nltk(args.nltk_data.resolve(), staging)
        for name in (run.name, "nltk_data"):
            replace(staging / name, MODEL_ROOT / name)
            replaced.append(name)
    except (BundleError, OSError, ValueError) as error:
        changed = ", ".join(replaced) or "không có gì"
        print(f"Đóng gói thất bại ({error}); đã thay trong web/model/: {changed}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    print(f"Đã đóng gói {run.name} vào {MODEL_ROOT / run.name}")
    print(f"manifest_sha256 = {hashlib.sha256(manifest_bytes).hexdigest()}")
    print(f"Web phục vụ run này khi RUN_PATH (web/backend/policy.py) là model/{run.name} "
          "hoặc IAP_WEB_RUN_PATH trỏ tới thư mục trên.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
