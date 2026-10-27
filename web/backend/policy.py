"""Read the same policy and response schema used by the Next proxy."""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load_configuration(root=ROOT):
    """Broken administrator-owned configuration must not prevent liveness."""
    documents = []
    for name in ("transport-policy.json", "analysis.schema.json", "transport-policy.schema.json", "explanation-factors.json"):
        try:
            document = json.loads((root / "web/contracts" / name).read_text(encoding="utf-8"))
            documents.append(document if isinstance(document, dict) else {})
        except (OSError, ValueError, UnicodeError):
            documents.append({})
    return tuple(documents)


POLICY, SCHEMA, POLICY_SCHEMA, FACTORS = load_configuration()
# Correlation syntax remains usable when the configuration is broken. No inference
# limits are substituted: no worker is started until all shared documents validate.
UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
UUID = re.compile(UUID_PATTERN)
UNAVAILABLE_ERROR = {"http": 503, "retryAfterSeconds": 5, "message": "Analysis is unavailable. Try again later."}
# Run 19-10 (train.py --mode baseline) mà web phục vụ, tương đối từ ROOT. runs/ không
# nằm trong git: máy khác phải train run tương ứng (hoặc đặt IAP_WEB_RUN_PATH), nếu
# không worker sẽ không sẵn sàng. None nghĩa là chưa cấu hình.
RUN_PATH = "runs/2026-10-23_web2"
# Biến môi trường ghi đè RUN_PATH; tiến trình con spawn kế thừa nên test dùng được run fixture.
RUN_PATH_ENV = "IAP_WEB_RUN_PATH"


def pinned_run():
    return os.environ.get(RUN_PATH_ENV) or RUN_PATH


FACTOR_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
# Cùng quy tắc với validateFactors ở frontend: ASCII in được, không có khoảng trắng đầu/cuối.
FACTOR_TEXT = re.compile(r"^[\x21-\x7e](?:[\x20-\x7e]{0,78}[\x21-\x7e])?$")


def validate_factors(document):
    """Catalogue tên factor của explanation (AD-14): id hợp lệ, nhãn và ghi chú tiếng Anh ngắn."""
    factors = document.get("factors") if isinstance(document, dict) else None
    if (not isinstance(factors, dict) or not factors or set(document) != {"version", "factors"} or
            isinstance(document["version"], bool) or document["version"] != 1):
        raise ValueError("Invalid explanation factor catalogue")
    for key, entry in factors.items():
        if (not FACTOR_ID.fullmatch(key) or not isinstance(entry, dict) or not {"label"} <= set(entry) <= {"label", "note"} or
                not all(isinstance(text, str) and FACTOR_TEXT.fullmatch(text) for text in entry.values())):
            raise ValueError("Invalid explanation factor catalogue")


def validate_policy():
    from jsonschema import Draft7Validator
    if not POLICY_SCHEMA or not SCHEMA or not POLICY or not FACTORS:
        raise ValueError("Missing shared configuration")
    validate_factors(FACTORS)
    Draft7Validator.check_schema(POLICY_SCHEMA)
    Draft7Validator.check_schema(SCHEMA)
    Draft7Validator(POLICY_SCHEMA).validate(POLICY)
    definitions = SCHEMA["definitions"]
    if definitions["RequestId"]["pattern"] != UUID_PATTERN:
        raise ValueError("Incompatible request identity schema")
    validator = Draft7Validator(SCHEMA)
    for name in ("RequestId", "ErrorCode", "AnalysisSuccess", "AnalysisError", "AnalysisStatus"):
        if name not in definitions:
            raise ValueError("Incomplete response schema")
    request_id = "672f0ea9-e237-45cd-8c08-8710f89b8258"
    for label in ("legit", "spam_or_phishing", "phishing"):
        validator.validate({"analysis_status": "completed", "label": label})
    factor = next(iter(FACTORS["factors"]))
    validator.validate({"analysis_status": "completed", "label": "phishing", "explanation": {
        "factors": [{"factor": factor, "direction": "positive", "strength": 1.0}]}})
    validator.validate({"request_id": request_id, "phase": "unknown"})
    for code, entry in POLICY["errors"].items():
        validator.validate({"request_id": request_id, "error": {"code": code, "message": entry["message"]}})
    d, limits = POLICY["deadlines"], POLICY["limits"]
    if not (limits["fileBytes"] < limits["multipartBytes"] and
            d["backendMs"] < d["proxyMs"] < d["browserMs"] and
            d["backendReserveMs"] >= d["clockSkewMs"] + d["terminateMs"] + d["killReapMs"]):
        raise ValueError("Inconsistent transport bounds")
    inputs = {"INVALID_REQUEST", "EMAIL_TOO_LARGE", "EMPTY_EMAIL", "INVALID_EMAIL", "INSUFFICIENT_CONTENT", "RESOURCE_LIMIT"}
    for code, entry in POLICY["errors"].items():
        if (entry["retryAfterSeconds"] == 0) != (code in inputs):
            raise ValueError("Inconsistent recovery policy")


class Rejection(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)
