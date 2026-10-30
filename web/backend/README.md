# Local real-model service

Demo Windows cục bộ này phục vụ một run 19-10 do `train.py --mode baseline` tạo ra
(`dumped_models/classification/run_manifest.json`, schema 2). Run được pin bằng
`RUN_PATH` trong `web/backend/policy.py` hoặc biến môi trường `IAP_WEB_RUN_PATH`; đường
dẫn tương đối của cả hai đều tính từ thư mục `web/`, không phải thư mục gốc project.
Hiện pin `model/2026-10-23_web2`: bản đóng gói của `runs/2026-10-23_web2` (XGBoost, train
2026-10-23, có lemmatize và stopwords NLTK) do `web/scripts/bundle-run.py` chép vào
`web/model/`. `web/model/` không nằm trong git (khoảng 665 MB): chép hoặc nén cả `web/`
thì mang theo run; clone từ git thì phải chạy lại script đóng gói (cần run gốc) hoặc đặt
`IAP_WEB_RUN_PATH`, nếu không worker sẽ không sẵn sàng.

`web/` chạy độc lập, không cần phần còn lại của project: backend chỉ dùng import tương
đối trong package, đọc contracts, run và samples theo thư mục `web/`, và không import
module nào ở thư mục gốc (kể cả trong test).

Web không dùng `preprocess.py`/`pipeline_cache.py` ở thư mục gốc mà dùng bản sao đóng
băng trong `web/backend/frozen_pipeline/`: đúng từng byte code đã train run đang pin
(commit `dd166b2`). `web/backend/__init__.py` đặt thư mục này lên đầu `sys.path` trước
mọi lần import. Nhờ vậy pipeline gốc có thể cập nhật theo upstream (bản 23-10 thêm khử
làm rối văn bản) mà web vẫn chạy; đổi lại, kết quả trên web dùng tiền xử lý cũ. Không
sửa hay format lại hai file này: chữ ký tiền xử lý băm từng byte, và `.gitattributes`
tắt việc đổi xuống dòng cho chúng.

Web dùng classifier `selected_model` của manifest với ngưỡng chọn trên validation:
dương tính khi xác suất lớp 1 ≥ ngưỡng. Run `target_mode: phishing` trả `phishing`
(Phishing), run `broad` trả `spam_or_phishing` (Spam / phishing). Đây là ngoại lệ
local đã công bố: chỉ có bằng chứng validation, chưa qua E0 hay đánh giá chất lượng
trên tập test.

## Start locally

### Đóng gói run (một lần, trong repository đầy đủ)

`bundle-run.py` chỉ dùng thư viện chuẩn, chạy bằng Python nào cũng được. Nó kiểm SHA-256
của mọi artifact trong manifest ngay lúc chép, rồi chép `run_manifest.json`, các artifact
đó và dữ liệu NLTK đã dùng lúc train (`corpora/stopwords`, `corpora/wordnet.zip`; mặc định
lấy từ `.venv/nltk_data`, đổi bằng `--nltk-data`) vào `web/model/<run-id>/` và
`web/model/nltk_data/`. Mọi thứ được ghi vào một thư mục tạm rồi mới đổi tên vào chỗ: hash
sai hoặc thiếu file thì lệnh thoát với mã khác 0 và `web/model/` không đổi. Thư mục run và
`nltk_data` được thay bằng hai lần đổi tên riêng; nếu lần đổi tên `nltk_data` lỗi sau khi
thư mục run đã được thay, thông báo lỗi nêu rõ thư mục nào đã bị thay. `--run` và
`--nltk-data` tương đối tính từ thư mục hiện hành (khác `RUN_PATH`/`IAP_WEB_RUN_PATH`,
vốn tính từ `web/`).

```powershell
python web/scripts/bundle-run.py --run runs/2026-10-23_web2
```

`web/backend/__init__.py` đặt `web/model/nltk_data` lên đầu đường tìm của NLTK (biến
`NLTK_DATA`, tiến trình con kế thừa), nên stopwords và wordnet trùng lúc train kể cả trên
máy không có `.venv` gốc.

### Chạy độc lập từ `web/`

Dùng Python 3.11 và một virtualenv riêng `web/.venv` (git bỏ qua). `requirements.txt` gồm
`requirements-api.txt` và các gói ML khoá đúng phiên bản trong `.venv` gốc đã train run.
Generate a token in a Python-service PowerShell window, then start the service:

```powershell
cd web
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
$env:ML_API_TOKEN = (.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
$env:ML_API_TOKEN  # Display only in your local terminal to copy into the second window.
.venv/Scripts/python.exe -m backend
```

### Chạy từ thư mục gốc

Cách cũ vẫn dùng được với `.venv` gốc (đã có gói ML, chỉ cần thêm gói API). Backend vẫn
phục vụ run đã đóng gói trong `web/model/`; muốn dùng thẳng run trong `runs/` thì đặt
`$env:IAP_WEB_RUN_PATH = '../runs/2026-10-23_web2'` (tương đối từ `web/`). Hai cách cho
cùng `manifest_sha256` vì script đóng gói chép nguyên byte manifest.

```powershell
.venv/Scripts/python.exe -m pip install -r web/backend/requirements-api.txt
$env:ML_API_TOKEN = (.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
.venv/Scripts/python.exe -m web.backend
```

In a second PowerShell window, use the same generated token as the first window.
Copy it locally through the terminal; do not commit it or put it in a public variable:

```powershell
cd web/frontend
npm.cmd ci
$env:ML_API_URL = 'http://127.0.0.1:8000'
$env:ML_API_TOKEN = '<same generated token from the Python-service window>'
npm.cmd run dev
```

Wait for `/health/ready` to return HTTP 200 before the first Analyze. HTTP 503
while the verified worker is starting is expected; retry the readiness check. If
it stays unready, inspect the backend startup log and token, shared-policy and
trusted-model configuration before restarting. Liveness alone does not mean the
worker is ready.

Open `http://127.0.0.1:3000`. Select a file from `web/backend/samples/` and click Analyze.
Selection alone sends nothing. The result includes your selected filename and the
truthful mixed-target label. Samples have no expected label or quality claim.
Alternatively set these server-only values in ignored `web/frontend/.env.local`.
Neither variable may use the `NEXT_PUBLIC_` prefix. Empty/mismatched configuration
returns a safe unavailable error. Both services bind loopback; no publication is
part of this demo. Stop both consoles with Ctrl+C. The backend supports `--port`
for another local port; update `ML_API_URL` to match.

Readiness can take several seconds because startup verifies **all** run hashes and
matching test arrays before loading the three inference artifacts. Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-WebRequest http://127.0.0.1:8000/health/ready
```

Live returns `{"status":"alive"}`; ready returns `{"status":"ready"}` only after
verification, otherwise HTTP503 with `{"status":"unready"}`. A missing token,
unconfigured or wrong run, tampered/incompatible artifact or invalid shared policy leaves
liveness available and classification disabled. Repair startup configuration and
restart the service. Runtime child death, deadline or disconnect reaps the old child
before reloading the startup-pinned run; readiness remains unavailable during recovery.
Đường dẫn run chỉ được đọc lúc khởi động; thay đổi sau đó không được áp dụng cho tới
khi khởi động lại. Giữ nguyên mọi run hiện có.

## Runtime behavior

The supervisor authenticates one admitted request before consuming its body; it
rejects busy requests without a queue. One spawned resident child performs bounded
multipart/MIME parsing, feature extraction and prediction. Uploads stay in memory;
there is no upload spool, persistent email history or sensitive access/content log.
Links, remote images and attachments are never fetched or executed. The browser
contacts its same-origin Next proxy, which alone holds the Bearer token and forwards
the canonical filename `message.eml` with UUID/deadline headers.

Both services consume `web/contracts/transport-policy.json`: 2 MiB file, bounded
multipart, 100 MIME nodes, root depth 0 through 20, 2 MiB eligible decoded subject/body
UTF-8 and 50,000 final normalized tokens. Actual overflow rejects without truncation.
Parser defects are rejected. Attachments count as MIME nodes and file bytes, but
their text does not become body tokens or spend the eligible decoded-text budget.
The trusted proxy deadline is clamped to 60s backend execution with the 4s cleanup
reserve. Deadline/disconnect termination uses 1s TERM reap and 1s KILL reap; an
unreapable child terminates the supervisor without launching another child.
Status exposes only startup or matching current receiving/processing phase and
never a label, content, filename or history.

Trước khi sẵn sàng, adapter kiểm tra: manifest `status: complete` và schema 2; SHA-256
của mọi artifact; `settings.feature_names` trùng `preprocess.FEATURE_NAMES` (53
feature); chữ ký tiền xử lý ghi lúc train (`settings.preprocessing`) trùng
`pipeline_cache.preprocessing_signature()` hiện tại; `selected_model` là classifier
sklearn/XGBoost (BERT bị từ chối); kiểu, lớp `[0, 1]` và độ rộng (Doc2Vec +
53) của object đã nạp. Byte của từng file được kiểm tra lại trước khi unpickle;
danh sách global cho phép gồm Doc2Vec/numpy và module `sklearn.`/`xgboost.`. Chỉ hỗ
trợ file model cục bộ đáng tin; đây không phải sandbox cho pickle lạ.

Tiền xử lý và suy luận dùng chính code lúc train (bản đóng băng): `pipeline_cache._process` (trích
feature từ byte gốc trước khi làm sạch, lemmatization theo run) và
`preprocess.infer_document_vector` (alpha 0.025, min_alpha 0.0005, số epoch suy luận
của run, seed theo nội dung). Stopwords được cố định theo danh sách ghi trong run.
Scaler chỉ `transform`, vector Doc2Vec đứng trước feature đã chuẩn hoá. Một luồng
tính toán, hash seed 0 cho tiến trình con, khôi phục RNG Python/NumPy/Doc2Vec sau mỗi
request. Không tải tài nguyên, không fit, train hay evaluate trong request.

Explanation (FR-11, AD-14): khi `selected_model` là XGBoost và run có `target_mode:
phishing`, kết quả kèm `explanation.factors` gồm tối đa 5 factor `{factor, direction,
strength}`. Đây là đóng góp SHAP chính xác (`pred_contribs`) trên margin của đúng vector
đã cho ra nhãn: 100 chiều Doc2Vec gộp thành `text_content`, `direction` tính theo lớp 1,
`strength` là độ lớn tương đối so với factor mạnh nhất. Tên hiển thị tiếng Anh nằm trong
`web/contracts/explanation-factors.json` (`is_html` kèm ghi chú tạm "Known dataset bias"
cho tới khi quyết định Q9). Lúc khởi động, adapter kiểm tính cộng trên 256 dòng test đầu
và kiểm catalogue phủ đủ feature (sai thì không sẵn sàng, stage `EXPLANATION`); mỗi
request kiểm lại tính cộng, sai thì trả `INTERNAL_ERROR`. Classifier khác, run `broad`,
hoặc email mà mọi đóng góp đều bằng 0 thì chỉ trả nhãn. Factor không được ghi log và không có trong lỗi hay kênh status. Factor mô tả
model đang dựa vào đâu, không phải bằng chứng email độc hại.

The observed environment is Python 3.11.2 on native Windows; ML packages are
NumPy 2.4.6, SciPy 1.17.1, Gensim 4.4.0, scikit-learn 1.9.1, XGBoost 3.2.0 and
NLTK 3.10.3, installed directly in `.venv` at the same versions (the former
`project_legacy_packages.pth` link to a sibling `venv/` was removed on 2026-10-20).
`requirements.txt` khoá toàn bộ backend (API, gói ML và phụ thuộc gián tiếp) theo đúng
các phiên bản này; `requirements-api.txt` chỉ khoá phần API, dùng khi `.venv` gốc đã có
gói ML. Chữ ký tiền xử lý băm cả phiên bản nltk/beautifulsoup4, danh sách stopwords và
việc có wordnet hay không, nên môi trường lệch sẽ bị từ chối (`MODEL_COMPATIBILITY`).
Không phân phối virtualenv; cài lại từ `requirements.txt`. Adapter
startup records manifest/code hashes, actual package versions and settings in
transient supervisor metadata for local verification without widening HTTP results.

## Verify and upgrade

```powershell
.venv/Scripts/python.exe -m unittest discover -s web/backend/tests -v
# Hoặc trong web/ (kể cả bản chép riêng), với web/.venv:
#   .venv/Scripts/python.exe -m unittest discover -s backend/tests -v
cd web/frontend
npm.cmd run contracts:check
npm.cmd test
npm.cmd run lint
npm.cmd run build
$env:PLAYWRIGHT_CHANNEL = 'msedge'
npm.cmd run test:integration
npm.cmd run test:real-model
npm.cmd run test:browser
```

Test backend dùng một run 19-10 nhỏ (khoảng 1,5 MB) train trên email tổng hợp, commit sẵn
trong `web/backend/tests/fixture_run/` (`web/.gitattributes` tắt đổi xuống dòng vì manifest
băm từng byte). Chúng chép run này vào thư mục tạm, trỏ `IAP_WEB_RUN_PATH` tới bản chép và
không import module nào ở thư mục gốc, nên chạy được cả từ thư mục gốc (`web.backend`) lẫn
từ `web/` (`backend`). Khi đổi bản đóng băng hoặc email tổng hợp, tạo lại fixture trong
repository đầy đủ bằng `.venv/Scripts/python.exe web/backend/tests/build_fixture.py` (train
qua `train.py` gốc với hai module đóng băng và `PYTHONHASHSEED=0` như worker, vì vector
Doc2Vec phụ thuộc hash seed). Chúng kiểm tra vector/nhãn lúc phục vụ trùng mảng test
lúc train, và các ca run chưa cấu hình, chưa hoàn tất, artifact bị sửa, lệch schema
hoặc tiền xử lý, BERT được chọn. Nhóm test `Explanation` dùng bản sao fixture chọn
XGBoost để so factor với đóng góp tính độc lập, kiểm lặp lại/đảo thứ tự/khởi động lại và
các ca fail closed. `test:real-model` khởi động backend bằng `python -m backend` từ
`web/`, với Python lấy từ biến `IAP_WEB_PYTHON` (nếu có), rồi `web/.venv`, rồi `.venv` gốc; nó cần run đã
đóng gói (hoặc `IAP_WEB_RUN_PATH`) và yêu cầu run đó trả explanation.

Edge is installed on the tested workstation. For another installed browser select
its Playwright channel, or install Playwright Chromium. `test:real-model` starts actual
loopback web/backend/Next processes and checks five MIME samples through real API,
proxy and browser plus unavailable-result clearing; nó chỉ cần `web/` có run đã đóng gói.
The frontend-only `test:integration` checks transport serialization with a clearly
marked fixture backend. Browser regression fixtures
remain marked samples. Backend tests compare vector hashes and labels for five
emails under repeat, reorder and restarted child; they also exercise auth,
identity, limits, busy admission, artifact/readiness and recovery failures.
Process/network/browser execution may require sandbox approval. These checks
establish demo operation, not model quality, E0, Linux/Docker portability or cloud
timing/memory acceptance. Existing offline tests are assessed separately.

Đổi sang run mới: train bằng `train.py --mode baseline --output runs/<tên>` với code
hiện tại, chép nguyên byte `preprocess.py` và `pipeline_cache.py` ở thư mục gốc (đúng
bản đã train run đó) đè lên hai file trong `web/backend/frozen_pipeline/`, đóng gói bằng
`python web/scripts/bundle-run.py --run runs/<tên>`, đặt `RUN_PATH = "model/<tên>"` (hoặc
`IAP_WEB_RUN_PATH`), tạo lại fixture bằng `build_fixture.py`, chạy test backend rồi khởi
động lại. `train.py` mặc
định train cả BERT; nếu BERT được chọn trên validation thì web từ chối khởi động
(`MODEL_COMPATIBILITY`), nên với run dành cho web hãy thêm `--skip-text-training`. Sửa
hai file đóng băng làm đổi chữ ký tiền xử lý, nên run đang pin sẽ bị từ chối. Nhãn `phishing` hiện dựa trên bằng chứng validation;
E0 vẫn cần rà soát nguồn nhãn và đánh giá độc lập. Giữ nguyên ranh giới HTTP và luồng
frontend; muốn quay lại run trước thì đặt lại `RUN_PATH` (cùng code tiền xử lý đã
train run đó). Xem [ngoại lệ local](../../_bmad-output/specs/spec-iap-web-application/local-demo.md).
