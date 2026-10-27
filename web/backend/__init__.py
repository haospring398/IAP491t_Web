"""Local legacy inference demo; no training or evaluation side effects."""
import sys
from pathlib import Path

# Web dùng preprocess.py/pipeline_cache.py đóng băng cùng run đang pin, không dùng bản ở
# thư mục gốc: đặt thư mục này lên đầu sys.path trước mọi lần import hai module đó.
FROZEN_PIPELINE = Path(__file__).resolve().parent / "frozen_pipeline"
if str(FROZEN_PIPELINE) not in sys.path:
    sys.path.insert(0, str(FROZEN_PIPELINE))
