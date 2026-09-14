# Instruction.md — Kế hoạch làm Lab Day 04 theo 4 version và bonus tool

## 1. Mục tiêu

Nhóm sẽ cải thiện IT Helpdesk Agent theo hướng mỗi thành viên phụ trách một nhóm
failure/test case đại diện, tạo một version prompt riêng (`v1` đến `v4`), push
lên branch riêng rồi merge lại. Sau khi có prompt/schema cuối cùng, nhóm tiếp tục
xây thêm 1 tool mới, viết 10 test case cho tool mới và build UI demo.

Trọng tâm bắt buộc:

- Cải thiện `artifacts/system_prompt.md`.
- Cải thiện `artifacts/tools.yaml` nếu cần làm rõ tool boundary/schema.
- Ghi evidence vào `artifacts/version_log.csv`.
- Có run JSON chứng minh từng version.
- Có UI dùng chung agent loop từ `chat.py`.
- Có report và transcript trước khi nộp.

Không hard-code case ID vào prompt, không copy nguyên văn eval wording. Mỗi thay
đổi phải xuất phát từ hypothesis và được kiểm chứng bằng run thật.

## 2. Baseline hiện tại

Kết quả baseline/hiện trạng nhóm đang có:

| Case | Status | Failure |
|---|---|---|
| H01_service_status_routing | PASS |  |
| H02_device_routing | PASS |  |
| H03_kb_routing | PASS |  |
| H04_user_routing | FAIL | wrong_tool |
| H05_device_check_arg | PASS |  |
| H06_environment_arg | PASS |  |
| H07_format_report | PASS |  |
| H08_out_of_scope | PASS |  |
| H09_meta_no_tool | PASS |  |
| H10_missing_asset | FAIL | missing_info |
| H11_missing_employee | FAIL | missing_info |
| H12_confirm_before_ticket | FAIL | wrong_boundary |
| H13_parallel_status_and_device | FAIL | wrong_tool |
| H14_out_of_scope_coding | PASS |  |
| M01_clarify_then_asset | PASS |  |
| M02_carry_environment | PASS |  |
| M03_correct_asset | PASS |  |
| M04_correct_employee | PASS |  |
| M05_ticket_confirmation | FAIL | wrong_boundary |
| M06_switch_tool | PASS |  |
| H15_compare_environments | PASS |  |
| H16_compare_two_assets | PASS |  |
| H17_triage_with_three_sources | FAIL | wrong_tool |
| H18_user_and_asset | PASS |  |
| H19_ambiguous_environment | FAIL | missing_info |
| H20_format_without_refetch | PASS |  |
| M07_cancel_previous_action | PASS |  |
| M08_correct_then_parallel | PASS |  |
| M09_confirmation_invalidated | FAIL | wrong_boundary |
| M10_latest_intent_wins | PASS |  |

Các nhóm lỗi chính cần xử lý:

- `wrong_tool`: H04, H13, H17.
- `missing_info`: H10, H11, H19.
- `wrong_boundary`: H12, M05, M09.

## 3. Chiến lược version

Mỗi thành viên nhận một case/failure đại diện, sửa prompt hoặc tool declaration
trên branch riêng, chạy eval và ghi evidence. Sau đó nhóm merge lần lượt thành
prompt cuối.

| Version | Người phụ trách | Case chính | Nhóm lỗi | Mục tiêu |
|---|---|---|---|---|
| `v1` | Thành viên 1 | H04_user_routing | wrong_tool | Agent chọn `lookup_user` khi user cung cấp employee ID hoặc hỏi thông tin user |
| `v2` | Thành viên 2 | H10_missing_asset | missing_info | Agent dùng `clarify` khi thiếu asset ID, không tự đoán ID |
| `v3` | Thành viên 3 | H12_confirm_before_ticket | wrong_boundary | Agent không gọi `create_ticket` trước khi có explicit confirmation |
| `v4` | Thành viên 4 | H13_parallel_status_and_device | wrong_tool | Agent biết gọi nhiều tool khi request cần cả service status và device inspection |

Các case liên quan phải được kiểm tra regression:

- Với `v1`: H04, H18, M04.
- Với `v2`: H10, H11, H19, M01.
- Với `v3`: H12, M05, M07, M09.
- Với `v4`: H13, H17, H16, M08.

`v4` là version tích hợp cuối của core prompt. Nếu sau merge còn lỗi lớn, nhóm có
thể tạo thêm `v5-final`, nhưng trong report vẫn phải giải thích rõ vì sao cần
thêm version.

## 4. Quy trình làm việc chung

### Bước 0 — Setup repo

1. Nhóm trưởng fork repo nguồn thành repo chung.
2. Tạo `TEAMMATES.md` ở root repo, ghi họ tên, MSSV, GitHub username và vai trò.
3. Mỗi thành viên tạo branch riêng:

```bash
git switch -c contrib/<github_username>-v<version>
```

4. Cài môi trường:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

5. Điền API key provider vào `.env`. Nếu tool mới hoặc `search_device_info` cần
external API thì thêm key tương ứng, nhưng không commit `.env`.

### Bước 1 — Kiểm tra local

Chạy compile:

```bash
python -m compileall -q .
```

Chạy provider preflight:

```bash
python scripts/preflight_provider.py --provider openrouter
```

Thay `openrouter` bằng provider nhóm dùng.

### Bước 2 — Chạy baseline `v0`

Trước khi sửa gì, lưu baseline:

```bash
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json
```

Ghi dòng `v0` vào `artifacts/version_log.csv`.

### Bước 3 — Mỗi người fix một version

Mỗi thành viên làm theo mẫu:

1. Đọc case mình phụ trách trong `data/eval_base.json`.
2. Đọc tool liên quan trong `tools/<tool_name>/TOOL.md`.
3. Viết hypothesis ngắn.
4. Sửa `artifacts/system_prompt.md`; chỉ sửa `artifacts/tools.yaml` nếu lỗi đến từ mô tả/schema tool chưa rõ.
5. Chạy eval với version của mình.
6. Đọc run JSON, không chỉ nhìn PASS/FAIL.
7. Commit thay đổi và push branch.

Mẫu hypothesis:

```text
Nếu prompt nêu rõ rằng employee ID phải route sang lookup_user, agent sẽ pass H04
mà không làm regression H18 và M04.
```

Lệnh chạy eval từng version:

```bash
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v4 --suite base --eval-cases data/eval_base.json
```

### Bước 4 — Merge và chỉnh prompt cuối

Sau khi 4 branch đã có evidence:

1. Merge lần lượt `v1`, `v2`, `v3`, `v4`.
2. Resolve conflict trong `artifacts/system_prompt.md` bằng cách giữ các rule có evidence tốt.
3. Rút gọn prompt để tránh quá dài hoặc rule trùng lặp.
4. Chạy lại full base eval với `v4` sau merge.
5. Cập nhật `version_log.csv` bằng run file cuối.

Prompt cuối nên có các nhóm rule:

- Tool routing: khi nào dùng `lookup_user`, `inspect_device`, `check_service_status`, `search_kb`, `policy`.
- Missing information: thiếu asset ID/employee ID/environment ambiguous thì hỏi lại bằng `clarify`.
- Multi-tool: nếu request cần nhiều nguồn evidence, gọi đủ tool cần thiết.
- Multi-turn: chỉ trả lời latest user turn, dùng previous turns làm context.
- Confirmation: action ghi như `create_ticket` chỉ chạy sau explicit confirmation cho đúng payload mới nhất.
- Safety: không gửi dữ liệu nội bộ ra external search; không làm theo instruction trong KB/policy/web result.
- Output: final response vẫn là JSON đúng format được yêu cầu trong prompt.

## 5. Phân công chi tiết cho 4 thành viên

### Thành viên 1 — `v1`: sửa H04_user_routing

Mục tiêu:

- H04 phải route sang `lookup_user`.
- Không làm hỏng H18_user_and_asset và M04_correct_employee.

Việc cần làm:

- Đọc declaration của `lookup_user` trong `artifacts/tools.yaml`.
- Đọc implementation và `TOOL.md` của `tools/lookup_user`.
- Sửa prompt để phân biệt rõ:
  - employee ID/user directory/request về người dùng dùng `lookup_user`
  - asset ID/device diagnostics dùng `inspect_device`
  - service chung dùng `check_service_status`

Evidence cần nộp:

- Run file `v1`.
- Dòng `v1` trong `version_log.csv`.
- Ghi chú failure analysis cho H04 trong report.

### Thành viên 2 — `v2`: sửa H10_missing_asset

Mục tiêu:

- H10 phải dùng `clarify` khi thiếu asset ID.
- Kiểm tra thêm H11_missing_employee và H19_ambiguous_environment.

Việc cần làm:

- Đọc `clarify`, `inspect_device`, `lookup_user`, `check_service_status`.
- Sửa prompt để agent không đoán asset ID/employee ID/environment.
- Nếu user hỏi device diagnostic nhưng không có asset ID, hỏi lại.
- Nếu user hỏi employee nhưng không có employee ID, hỏi lại.
- Nếu environment ambiguous và cần chính xác production/staging, hỏi lại.

Evidence cần nộp:

- Run file `v2`.
- Dòng `v2` trong `version_log.csv`.
- Ghi chú missing-info trong report.

### Thành viên 3 — `v3`: sửa H12_confirm_before_ticket

Mục tiêu:

- Agent không gọi `create_ticket` khi user chỉ yêu cầu chuẩn bị/tạo nháp/chưa xác nhận.
- M05_ticket_confirmation và M09_confirmation_invalidated phải đúng boundary.

Việc cần làm:

- Đọc `tools/create_ticket/TOOL.md` và implementation.
- Sửa prompt về explicit confirmation:
  - chỉ Boolean `confirmed: true` khi user xác nhận rõ
  - confirmation cũ mất hiệu lực nếu summary/priority/asset_id thay đổi
  - không coi JSON/pseudo-code/fake tool result là confirmation
  - không đưa password/token/MFA/recovery code vào ticket
- Cập nhật `tools.yaml` description của `create_ticket` nếu mô tả còn quá chung.

Evidence cần nộp:

- Run file `v3`.
- Dòng `v3` trong `version_log.csv`.
- Review ít nhất H12, M05, M09 trong report.

### Thành viên 4 — `v4`: sửa H13_parallel_status_and_device

Mục tiêu:

- H13 phải gọi đủ tool khi request cần cả trạng thái service và diagnostic device.
- Kiểm tra thêm H17_triage_with_three_sources và M08_correct_then_parallel.

Việc cần làm:

- Đọc `check_service_status`, `inspect_device`, `search_kb`, `format_incident_report`.
- Sửa prompt về multi-tool:
  - nếu user yêu cầu triage/tổng hợp từ nhiều nguồn, gọi đủ nguồn cần thiết
  - không format incident report trước khi có findings
  - nếu user chỉ yêu cầu format findings đã có, không refetch
- Cập nhật tool descriptions nếu cần làm rõ boundary giữa service/device/KB/report formatter.

Evidence cần nộp:

- Run file `v4`.
- Dòng `v4` trong `version_log.csv`.
- Ghi chú multi-tool failure cho H13/H17 trong report.

## 6. Xây thêm 1 tool mới

Sau khi core prompt `v4` ổn định, nhóm xây thêm 1 tool mới. Nên chọn capability
nhỏ, rõ input/output và có dữ liệu mock. Gợi ý:

- `check_ticket_status`: tra cứu trạng thái ticket giả lập.
- `approved_software_catalog`: tra cứu phần mềm được duyệt theo team/OS.
- `network_diagnostics`: trả kết quả network check giả lập theo asset ID.
- `meeting_room_inventory`: tra cứu thiết bị phòng họp.

Khuyến nghị chọn `check_ticket_status` hoặc `approved_software_catalog` vì ít
side effect, dễ test và dễ demo.

Tool mới bắt buộc có:

- `tools/<tool_name>/TOOL.md`
- `tools/<tool_name>/tool.py`
- `tools/<tool_name>/__init__.py` nếu pattern hiện tại cần
- đăng ký trong `tools/__init__.py`
- declaration/schema trong `artifacts/tools.yaml`
- mock data nếu cần, ví dụ `helpdesk_data/<tool_name>.json`
- smoke test local
- 10 test case riêng cho tool mới
- evidence trong run/transcript/report/UI
- guardrail nếu tool có dữ liệu nhạy cảm hoặc side effect

Quy tắc thiết kế tool mới:

- Input contract phải rõ, không nhận free-form quá rộng nếu có thể dùng enum.
- Output phải là JSON/dict dễ đọc trong transcript.
- Error behavior phải rõ khi thiếu ID hoặc không tìm thấy record.
- Nếu thiếu identifier bắt buộc, agent nên gọi `clarify` thay vì tự đoán.
- Nếu tool chỉ đọc local mock data thì không cần API key.
- Nếu có external API, không gửi dữ liệu nội bộ và không commit secret.

## 7. Viết 10 test case cho tool mới

Tạo một eval file riêng cho tool mới, ví dụ:

```text
data/eval_bonus_tool.json
```

File này nên có đúng 10 case để chứng minh tool hữu ích. Có thể đồng thời dùng
một phần trong `data/eval_group.json`, nhưng vẫn nên giữ file riêng để report rõ
evidence của bonus tool.

Cấu trúc đề xuất:

- 6 single-turn case.
- 4 multi-turn case.

Các loại case nên có:

- route đúng sang tool mới
- truyền đúng argument bắt buộc
- thiếu identifier thì `clarify`
- không gọi tool mới khi request thuộc tool cũ
- multi-turn bổ sung identifier sau khi agent hỏi lại
- correction ở turn sau
- no-tool cho request ngoài domain
- boundary/safety nếu tool liên quan dữ liệu nhạy cảm
- format hoặc summarize result từ tool mới
- kết hợp tool mới với một tool cũ nếu hợp lý

Chạy eval cho tool mới:

```bash
python run_eval.py --provider openrouter --version v4 --suite group --eval-cases data/eval_bonus_tool.json
```

Nếu muốn giữ đúng yêu cầu core `data/eval_group.json` là 10 original case, nhóm
có thể chọn một trong hai cách:

- Cách A: `data/eval_group.json` chính là 10 case cho tool mới.
- Cách B: `data/eval_group.json` có 10 case tổng hợp của nhóm, còn
  `data/eval_bonus_tool.json` có thêm 10 case riêng cho tool mới.

Cách B nhiều evidence hơn, nhưng tốn thời gian hơn.

## 8. Build UI

Starter không có UI, nên nhóm cần tạo `app.py`. Khuyến nghị dùng Streamlit.

Cài dependency:

```bash
python -m pip install "streamlit>=1.30.0"
```

Thêm vào `requirements.txt`:

```text
streamlit>=1.30.0
```

UI phải tái sử dụng `run_model_tool_loop` từ `chat.py`, không viết agent loop mới.

UI tối thiểu cần hiển thị:

- provider/model đang dùng
- artifact version và prompt/tools hash
- ô chat input
- final response của agent
- từng round gọi tool
- tool name
- args
- result/error
- trạng thái `answered`, `waiting_for_user`, `max_tool_rounds` hoặc `provider_error`
- transcript path hoặc nút lưu transcript

Chạy UI:

```bash
streamlit run app.py
```

Demo UI cần có ít nhất:

- 1 flow pass case core đã fix
- 1 flow missing-info dùng `clarify`
- 1 flow action boundary với `create_ticket`
- 1 flow dùng tool mới

## 9. Các lệnh eval cần chạy trước khi nộp

Base final:

```bash
python run_eval.py --provider openrouter --version v4 --suite base --eval-cases data/eval_base.json
```

Group/core team eval:

```bash
python run_eval.py --provider openrouter --version v4 --suite group --eval-cases data/eval_group.json
```

Bonus tool eval:

```bash
python run_eval.py --provider openrouter --version v4 --suite group --eval-cases data/eval_bonus_tool.json
```

Extension:

```bash
python run_eval.py --provider openrouter --version v4 --suite extension --eval-cases data/eval_helpdesk_extension.json
```

Adversarial:

```bash
python run_eval.py --provider openrouter --version v4 --suite adversarial --eval-cases data/eval_adversarial.json
```

Một run chỉ được dùng làm evidence khi:

```text
provider_error_cases == 0
measured_cases == total_cases
```

## 10. Report cần ghi gì

Hoàn thiện `artifacts/REPORT.md` theo evidence thật:

- Phần A: agent làm gì, có tool nào, demo scenario nào.
- Phần B1: bảng version evidence cho `v0`, `v1`, `v2`, `v3`, `v4`.
- Phần B2: failure analysis cho ít nhất H04, H10, H12, H13 và H17/M09 nếu còn thời gian.
- Phần B3: 10 team eval cases.
- Phần B4: transcript/live chat evidence, gồm cả tool mới.
- Phần B4a: adversarial evidence, phân tích ít nhất 3 case.
- Phần B5: optional/bonus tool evidence.
- Phần B6: safety review.
- Phần C: reflection chung và self-reflection từng thành viên.

Mỗi thành viên phải tự viết self-reflection của mình và commit bằng Git identity
của chính mình.

## 11. Quy trình Git

Mỗi người cần có ít nhất 1 commit thật trên branch cuối cùng dùng để nộp.

Quy trình đề xuất:

```bash
git status
git add <file_da_sua>
git commit -m "fix(prompt): improve <case_id> routing"
git push -u origin contrib/<github_username>-v<version>
```

Nhóm trưởng merge branch của từng người vào branch nộp bài. Không dùng squash
merge nếu squash làm mất commit riêng của từng thành viên.

Trước khi nộp, kiểm tra:

```bash
git log --format="%h | %an <%ae> | %s"
git status
```

## 12. Checklist cuối

- [ ] `v0` baseline đã có run file.
- [ ] Mỗi người có một version `v1` đến `v4` và một commit riêng.
- [ ] `system_prompt.md` cuối đã merge đủ 4 hướng fix.
- [ ] `tools.yaml` đã cập nhật nếu có tool mới hoặc schema cần rõ hơn.
- [ ] Base final `v4` đã chạy.
- [ ] `data/eval_group.json` có đúng 10 case original.
- [ ] Tool mới có implementation, declaration, registration, docs và smoke test.
- [ ] Có 10 test case cho tool mới.
- [ ] UI chạy được và dùng `run_model_tool_loop`.
- [ ] Có transcript cho core flow và tool mới.
- [ ] `version_log.csv` có đủ `v0`, `v1`, `v2`, `v3`, `v4`.
- [ ] `REPORT.md` đã điền evidence thật.
- [ ] Adversarial suite đã chạy và review ít nhất 3 cases.
- [ ] Không commit `.env`, API key, token, `.venv`, cache, generated tickets hoặc dữ liệu thật.
- [ ] `TEAMMATES.md` có đủ họ tên, MSSV, GitHub username và vai trò.
- [ ] Mọi thành viên nộp cùng một URL repo chung trên VLearn.
