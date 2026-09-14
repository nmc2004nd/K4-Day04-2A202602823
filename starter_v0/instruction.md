# Instruction.md — Kế hoạch implement Lab Day 04 IT Helpdesk Agent

## 1. Mục tiêu chung

Nhóm cần cải thiện IT Helpdesk Agent trong `starter_v0/` để agent chọn đúng tool,
truyền đúng arguments, xử lý hội thoại nhiều lượt và tôn trọng boundary an toàn.

Trong core lab, trọng tâm là cải thiện có evidence hai artifact:

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`

Không hard-code case ID, không copy nguyên văn eval wording vào prompt/schema.
Mỗi thay đổi cần có hypothesis, run evidence và ghi vào `artifacts/version_log.csv`.

## 2. Đầu ra bắt buộc

Nhóm cần hoàn thành các deliverable sau:

| Deliverable | Yêu cầu |
|---|---|
| `artifacts/system_prompt.md` | Prompt cuối cùng rõ routing, arguments, multi-turn, confirmation và safety boundary |
| `artifacts/tools.yaml` | Tool descriptions/schema rõ ràng, đồng bộ với implementation trong `tools/` |
| `artifacts/version_log.csv` | Có `v0`, `v1`, `v2`, `v3`, hypothesis, metric, run file và artifact hash |
| Base runs | Run JSON cho baseline và các version cải tiến |
| `data/eval_group.json` | Đúng 10 case original: 5 single-turn và 5 multi-turn |
| Adversarial evidence | Chạy fixed adversarial suite và review ít nhất 3 security cases |
| Transcript | Có evidence cho normal, missing-info, multi-turn và action boundary |
| UI | Chat chạy được, hiện tool calls, args, result/error và artifact version |
| `artifacts/REPORT.md` | Hoàn thành report dựa trên evidence thật |
| `TEAMMATES.md` | Nằm ở root repo chung, có họ tên, MSSV, GitHub username và vai trò |

Một run chỉ được tính là evidence hợp lệ khi:

```text
provider_error_cases == 0
measured_cases == total_cases
```

## 3. Luồng hoạt động cần implement

### Bước 0 — Repo và môi trường

1. Nhóm trưởng fork repo nguồn thành repo chung của nhóm.
2. Tạo `TEAMMATES.md` ở root repo, ghi đủ thành viên và vai trò.
3. Mỗi thành viên clone repo chung, tạo branch riêng:

```bash
git switch -c contrib/<github_username>
```

4. Cài môi trường:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

5. Điền API key provider vào `.env`. Nếu dùng `search_device_info` thì thêm
`TAVILY_API_KEY`.

### Bước 1 — Đọc interface và data

Tất cả thành viên nên đọc nhanh:

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`
- `data/eval_base.json`
- `data/eval_helpdesk_extension.json`
- `data/eval_adversarial.json`
- `tools/<tool_name>/TOOL.md` với các tool mình phụ trách

Cần trả lời được 3 câu:

1. Model nhìn thấy instruction và tool declaration nào?
2. Tool implementation thật sự làm gì và trả về gì?
3. Evaluator đang so sánh tool name/args/no-tool như thế nào?

### Bước 2 — Kiểm tra local trước khi tốn quota model

Chạy compile:

```bash
python -m compileall -q .
```

Chạy smoke test cho local tools cần demo:

```bash
python -c "from tools import TOOL_FUNCTIONS as T; print(T['clarify']('Mã asset là gì?', 'text'))"
python -c "from tools import TOOL_FUNCTIONS as T; r=T['search_kb']('VPN macOS certificate','vpn',2); print({'error':r.get('error'),'results':len(r.get('results') or []),'boundary':r.get('trust_boundary')})"
python -c "from tools import TOOL_FUNCTIONS as T; print(T['check_service_status']('vpn','production'))"
python -c "from tools import TOOL_FUNCTIONS as T; print(T['inspect_device']('LT-318','vpn'))"
python -c "from tools import TOOL_FUNCTIONS as T; print(T['lookup_user']('EMP-1007'))"
python -c "from tools import TOOL_FUNCTIONS as T; print(T['format_incident_report']([{'label':'VPN','detail':'degraded'}],'brief','VPN incident'))"
python -c "from tools import TOOL_FUNCTIONS as T; r=T['policy']('dữ liệu nào được gửi ra external tool','external_tools',2); print({'error':r.get('error'),'results':len(r.get('results') or []),'boundary':r.get('trust_boundary')})"
python -c "from tools import TOOL_FUNCTIONS as T; print(T['create_ticket']('VPN dry run','low','LT-204',False))"
```

Chạy provider preflight:

```bash
python scripts/preflight_provider.py --provider openrouter
```

Thay `openrouter` bằng `openai`, `anthropic` hoặc `gemini` nếu nhóm dùng provider
khác.

### Bước 3 — Chạy baseline v0

Giữ nguyên starter artifacts khi chạy baseline:

```bash
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json
```

Sau run, ghi vào `artifacts/version_log.csv` dòng `v0` với metric và run file.
Chọn một số failure đại diện để phân tích:

- wrong-tool case
- wrong-argument case
- missing-information case
- multi-tool hoặc multi-turn case
- confirmation/security boundary case

Mẫu phân tích failure:

```text
Case:
Expected calls:
Actual calls:
Observed mismatch:
Tool execution result:
Giả thuyết nguyên nhân:
Artifact dự định sửa:
Metric dự kiến thay đổi:
Rủi ro regression:
```

### Bước 4 — Cải thiện v1, v2, v3 theo vòng nhỏ

Mỗi version chỉ nên bắt đầu bằng một hypothesis rõ.

Vòng làm việc:

1. Chọn một nhóm failure.
2. Viết hypothesis.
3. Sửa một artifact chính: `system_prompt.md` hoặc `tools.yaml`.
4. Chạy lại base eval.
5. So metric và đọc failed traces.
6. Ghi `version_log.csv`.
7. Kiểm tra regression trên các case đã pass.

Gợi ý version:

| Version | Trọng tâm đề xuất | Artifact chính |
|---|---|---|
| v1 | Routing giữa service status, device inspection, user lookup, KB và policy | `tools.yaml` + prompt ngắn |
| v2 | Argument convention, missing ID, multi-tool, multi-turn correction/cancellation | `system_prompt.md` |
| v3 | Confirmation, ticket boundary, external search privacy, prompt injection defense | `system_prompt.md` + `tools.yaml` |

Lệnh chạy lại base:

```bash
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

### Bước 5 — Viết team eval

File `data/eval_group.json` hiện đang trống. Nhóm phải viết đúng 10 case original:

- 5 single-turn
- 5 multi-turn

Nên bao phủ:

- ambiguous intent
- thiếu asset ID/employee ID
- correction ở turn sau
- cancellation
- hai tool cùng loại với args khác nhau
- multiple assets
- stale confirmation
- format-only request
- internal/external data boundary
- optional tool nếu nhóm có dùng

Chạy group eval:

```bash
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

### Bước 6 — Chạy extension và adversarial

Extension:

```bash
python run_eval.py --provider openrouter --version v3 --suite extension --eval-cases data/eval_helpdesk_extension.json
```

Adversarial:

```bash
python run_eval.py --provider openrouter --version v3 --suite adversarial --eval-cases data/eval_adversarial.json
```

Review adversarial không chỉ nhìn PASS/FAIL. Cần kiểm tra:

- tool nào đã được gọi
- có ticket file nào được tạo không
- external request có chứa asset ID, employee ID, serial, hostname, location hay diagnostics không
- retrieved text có bị coi như trusted instruction không
- fake SYSTEM/DEVELOPER/tool-result text có làm đổi hành vi không
- confirmation có gắn với payload mới nhất không

### Bước 7 — Implement UI

Starter không có UI. Nếu dùng Streamlit:

```bash
python -m pip install "streamlit>=1.30.0"
```

Thêm dependency vào `requirements.txt`.

UI nên tạo trong `app.py` và tái sử dụng `run_model_tool_loop` từ `chat.py`.
Không viết agent loop mới.

UI tối thiểu cần có:

- input chat của user
- final response
- từng tool name và args
- tool result/error
- round/status
- artifact version và hashes
- transcript path hoặc cách export transcript

Chạy UI:

```bash
streamlit run app.py
```

### Bước 8 — Transcript và demo

Chạy chat CLI hoặc UI để tạo transcript:

```bash
python chat.py --provider openrouter --version v3
```

Cần có evidence cho ít nhất:

- normal flow: user hỏi status/KB/device và agent gọi đúng tool
- missing-info flow: agent dùng `clarify` thay vì đoán ID
- multi-turn flow: agent chỉ trả lời latest turn, dùng context trước đó
- action boundary: agent chỉ gọi `create_ticket` khi có explicit confirmation đúng payload

Chọn 3–5 demo scenario đã rehearse và ghi fallback run/transcript vào report.

### Bước 9 — Report và reflection

Hoàn thiện `artifacts/REPORT.md`:

- Phần A: mô tả agent, tool list, câu hỏi mẫu, demo scenarios
- Phần B: version evidence, failure analysis, team eval, chat evidence, adversarial evidence, safety review
- Phần C: reflection chung, self-reflection từng thành viên, final checkout

Mỗi thành viên phải tự viết self-reflection của mình và commit bằng Git identity
của chính mình.

### Bước 10 — Submission

Trước khi nộp:

```bash
git log --format="%h | %an <%ae> | %s"
git status
```

Checklist:

- [ ] Repo chung mở được bằng URL sẽ nộp.
- [ ] `TEAMMATES.md` có đủ thành viên và MSSV.
- [ ] Mỗi thành viên có ít nhất một commit đã merge vào branch nộp bài.
- [ ] Có đầy đủ deliverable core lab.
- [ ] Không có `.env`, API key, token, `.venv`, cache, generated ticket hoặc dữ liệu thật.
- [ ] Nhóm trưởng và mỗi thành viên nộp cùng một URL repo chung trên VLearn.

## 4. Phân chia task cho nhóm 4 người

### Thành viên 1 — Prompt lead và baseline analysis

Phạm vi:

- Đọc `artifacts/system_prompt.md`, `data/eval_base.json`, run output.
- Chạy baseline `v0` và phân tích failure đại diện.
- Đề xuất và implement rules trong `system_prompt.md`.
- Đảm bảo prompt rõ về:
  - không đoán asset ID/employee ID
  - dùng latest user turn trong multi-turn
  - khi nào hỏi lại bằng `clarify`
  - khi nào cần nhiều tool
  - output JSON đúng top-level fields

Deliverable:

- Các commit sửa `artifacts/system_prompt.md`
- Phần B1/B2 trong `artifacts/REPORT.md`
- Dòng version log cho các version có prompt change

Definition of done:

- Có ít nhất 1 hypothesis prompt rõ ràng.
- Có run evidence trước/sau cho hypothesis đó.
- Không hard-code case ID hoặc copy eval wording.

### Thành viên 2 — Tool schema, tool boundary và safety

Phạm vi:

- Đọc `artifacts/tools.yaml` và `tools/*/TOOL.md`.
- Cải thiện description/schema của các tool:
  - `clarify`
  - `search_kb`
  - `check_service_status`
  - `inspect_device`
  - `lookup_user`
  - `format_incident_report`
  - `policy`
  - `create_ticket`
  - `search_device_info`
- Đồng bộ tool declaration với implementation.
- Review boundary:
  - confirmation thật cho `create_ticket`
  - không gửi dữ liệu nội bộ ra `search_device_info`
  - KB/policy/web result là untrusted content nếu có instruction-like text

Deliverable:

- Các commit sửa `artifacts/tools.yaml`
- Smoke test log hoặc ghi chú kết quả local tool checks
- Phần B4a/B6 safety trong `artifacts/REPORT.md`

Definition of done:

- `python -m compileall -q .` pass.
- `run_eval.py` không báo invalid expected tool.
- Adversarial review có ít nhất 3 cases được phân tích bằng tool calls và tool results.

### Thành viên 3 — Eval owner, metrics và report evidence

Phạm vi:

- Quản lý `runs/`, `artifacts/version_log.csv`, summary metrics.
- Viết `data/eval_group.json` đúng 10 case original:
  - 5 single-turn
  - 5 multi-turn
- Chạy base/group/extension/adversarial eval cho `v3`.
- Đọc run JSON để lấy evidence vào report.

Deliverable:

- `data/eval_group.json`
- `runs/*.json` hợp lệ cho base/group/extension/adversarial
- `artifacts/version_log.csv`
- Các bảng B1, B2, B3, B4 trong `artifacts/REPORT.md`

Definition of done:

- Tất cả run evidence được dùng có `provider_error_cases == 0`.
- `data/eval_group.json` đúng schema và có đủ 10 case.
- Version log có đầy đủ `v0`, `v1`, `v2`, `v3`.

### Thành viên 4 — UI, transcript, integration và submission

Phạm vi:

- Implement UI trong `app.py` bằng Streamlit hoặc cách tương đương.
- UI tái sử dụng `run_model_tool_loop` từ `chat.py`.
- Hiển thị user request, final response, tool calls, args, result/error, status,
artifact version/hash và transcript path.
- Chuẩn bị demo scenario và transcript.
- Quản lý repo chung, branch, PR/merge và final submission checklist.

Deliverable:

- `app.py`
- Update `requirements.txt` nếu thêm Streamlit
- `transcripts/*.transcript.json`
- `TEAMMATES.md` ở root repo
- Phần A, B4, C trong `artifacts/REPORT.md`

Definition of done:

- `streamlit run app.py` chạy được.
- Có transcript cho normal, missing-info, multi-turn và action boundary.
- Mỗi thành viên có commit riêng trên branch nộp bài.

## 5. Thứ tự tích hợp để tránh xung đột

1. Thành viên 3 chạy `v0` baseline trước khi ai sửa prompt/schema.
2. Thành viên 1 và 2 chia nhau sửa prompt/schema theo từng version, không sửa đồng thời cùng một file trên branch chính.
3. Sau mỗi version, thành viên 3 chạy eval và cập nhật `version_log.csv`.
4. Thành viên 4 làm UI trên branch riêng, chỉ merge sau khi `chat.py`/`run_model_tool_loop` đã ổn định.
5. Cả nhóm review adversarial và report trước khi nộp.

## 6. Ranh giới an toàn phải giữ

Agent phải:

- Không tự đoán asset ID hoặc employee ID.
- Không yêu cầu, lưu hoặc đưa vào ticket password, token, API key, MFA/OTP, recovery code.
- Không coi pseudo-code, JSON user nhập, fake tool result là confirmation.
- Vô hiệu confirmation cũ nếu payload action thay đổi.
- Không gọi tool không được declare.
- Không làm theo instruction nằm trong KB, policy hoặc web result.
- Chỉ gửi manufacturer, public model và query type ra external search.
- Không gửi asset ID, employee ID, serial, hostname, location, assigned user, diagnostics hoặc ticket content ra external search.

## 7. Bonus tool nếu còn thời gian

Bonus không bắt buộc. Chỉ làm sau khi core lab đã có evidence ổn định.

Một bonus tool hợp lệ cần có:

- `tools/<tool_name>/TOOL.md`
- implementation chạy được
- đăng ký trong `tools/__init__.py`
- declaration/schema trong `artifacts/tools.yaml`
- mock data hoặc API setup phù hợp
- smoke test
- team eval case
- evidence trong UI/transcript/report
- guardrail theo side effect và dữ liệu

Không tính bonus nếu chỉ đổi tên tool cũ hoặc tạo folder rỗng.

## 8. Final checklist nhanh

- [ ] Compile pass.
- [ ] Local tool smoke tests pass.
- [ ] Provider preflight pass.
- [ ] Base v0 đã chạy và ghi log.
- [ ] V1, v2, v3 có hypothesis và metric.
- [ ] Group eval có đúng 10 case.
- [ ] Extension/adversarial đã chạy hoặc ghi rõ nếu không dùng optional external.
- [ ] UI chạy được và dùng chung agent loop.
- [ ] Report có evidence file cụ thể.
- [ ] Không commit secret, `.env`, `.venv`, cache, generated tickets.
- [ ] Mỗi thành viên có commit riêng và self-reflection riêng.
- [ ] Tất cả thành viên nộp cùng URL repo chung lên VLearn.
