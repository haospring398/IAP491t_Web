"""Local legacy inference demo; no training or evaluation side effects."""
import os
import sys
from pathlib import Path

# Web dùng preprocess.py/pipeline_cache.py đóng băng cùng run đang pin, không dùng bản ở
# thư mục gốc: đặt thư mục này lên đầu sys.path trước mọi lần import hai module đó.
FROZEN_PIPELINE = Path(__file__).resolve().parent / "frozen_pipeline"
if str(FROZEN_PIPELINE) not in sys.path:
    sys.path.insert(0, str(FROZEN_PIPELINE))

# Dữ liệu NLTK đóng gói cùng run (web/scripts/bundle-run.py) được tìm trước mọi thư mục
# khác. Đặt qua NLTK_DATA trước khi import nltk; tiến trình con spawn kế thừa biến này.
NLTK_DATA = Path(__file__).resolve().parents[1] / "model" / "nltk_data"
if NLTK_DATA.is_dir():
    _paths = [p for p in os.environ.get("NLTK_DATA", "").split(os.pathsep) if p]
    if str(NLTK_DATA) not in _paths:
        os.environ["NLTK_DATA"] = os.pathsep.join([str(NLTK_DATA), *_paths])
    if "nltk.data" in sys.modules and str(NLTK_DATA) not in sys.modules["nltk.data"].path:
        sys.modules["nltk.data"].path.insert(0, str(NLTK_DATA))
