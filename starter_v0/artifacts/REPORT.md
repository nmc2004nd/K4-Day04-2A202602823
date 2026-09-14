# Day 04 Lab v3 Report — IT Helpdesk Agent

## Team

- Team:
- Members:
- Provider/model:

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Viết 1–2 câu mô tả capability và giới hạn của agent.

**Link dùng thử:**

> URL:

## A2. Tool agent có

| Tool | Chức năng | Core / optional / team-built |
|---|---|---|
| clarify | Hỏi bổ sung hoặc xác nhận | core |
| approved_software_catalog | Tra cứu danh mục phần mềm được duyệt theo team, OS và category | team-built |
|  |  |  |

## A3. Câu hỏi mẫu

1.
2.
3.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

# PHẦN B — Chi tiết và evidence

Metric chỉ hợp lệ khi `provider_error_cases == 0`, `measured_cases ==
total_cases`, và tool result error đã được review thủ công.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run file |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 | Làm rõ missing-info trong `system_prompt.md` và boundary của `clarify`/`inspect_device`/`lookup_user`/`check_service_status` trong `tools.yaml` | Nếu agent không đoán asset ID, employee ID hoặc environment chưa rõ, H10/H11/H19 sẽ chuyển sang `clarify` và M01 vẫn dùng asset ID đã bổ sung | missing_info_related_cases | 0.25 | 1.00 | `runs/v2_B_base_openai_20260914T185738334210.json` |
| v3 |  |  |  |  |  |  |
| v4 | Thêm `approved_software_catalog`, mock data, schema và 10 group eval case | Nếu tool catalog có contract team/OS/category rõ, agent sẽ route đúng yêu cầu phần mềm được duyệt và không nhầm sang KB/policy | group_case_accuracy |  | 1.00 | `runs/v4_B_group_openai_20260914T191129935783.json` |

## B2. Failure analysis

| Case ID | Failure type | Actual calls | What failed | Fix |
|---|---|---|---|---|
| H10_missing_asset | missing_info | Sau fix: `clarify(response_type="text")` | Request chỉ nói "laptop của mình", chưa có asset ID nên không đủ điều kiện gọi `inspect_device` | Prompt yêu cầu hỏi lại khi thiếu asset ID cụ thể |
| H11_missing_employee | missing_info | Sau fix: `clarify(response_type="text")` | Request chỉ nêu phòng ban Sales, chưa có employee ID nên không đủ điều kiện gọi `lookup_user` | Prompt yêu cầu hỏi lại khi thiếu employee ID cụ thể |
| H19_ambiguous_environment | missing_info | Sau fix: `clarify(response_type="choice", options=["production", "staging"])` | "demo của team QA" không map chắc chắn sang `production` hoặc `staging` | Prompt yêu cầu hỏi chọn môi trường khi environment không thuộc enum |

## B3. Team eval cases

Liệt kê đúng 10 case tự viết: 5 single-turn và 5 multi-turn.

| Case ID | What it tests | Expected behavior | Result |
|---|---|---|---|
| G01_catalog_vpn_engineering_macos | Route câu hỏi phần mềm VPN được duyệt | `approved_software_catalog(team=engineering, os_family=macos, category=vpn)` | PASS |
| G02_catalog_browser_sales_windows | Trích đúng team/OS/category | `approved_software_catalog(team=sales, os_family=windows, category=browser)` | PASS |
| G03_catalog_design_macos | Map Mac sang `macos` | `approved_software_catalog(team=design, os_family=macos, category=design)` | PASS |
| G04_catalog_missing_os | Thiếu OS family | `clarify(response_type=choice, options=[windows, macos, linux])` | PASS |
| G05_catalog_not_kb_howto | Không dùng catalog cho hướng dẫn cấu hình | `search_kb(category=email)` | PASS |
| G06_catalog_out_of_scope | Không gọi tool khi ngoài helpdesk | no tool | PASS |
| G07_catalog_multiturn_fill | Multi-turn bổ sung team và OS/category | `approved_software_catalog(team=engineering, os_family=linux, category=development)` | PASS |
| G08_catalog_multiturn_correction | Correction ở lượt sau thắng context cũ | `approved_software_catalog(team=finance, os_family=windows, category=productivity)` | PASS |
| G09_catalog_asset_plus_catalog | Kết hợp tool mới với inspect device | `inspect_device` + `approved_software_catalog` | PASS |
| G10_catalog_policy_boundary | Latest policy intent thắng yêu cầu catalog cũ | `policy(policy_area=data_privacy)` | PASS |

## B4. Live chat evidence

| Scenario/turn | Version | Tool calls + args | Transcript/run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B4a. Adversarial evidence

Phân tích ít nhất 3 cases. Automatic score không chứng minh rằng không có dữ
liệu bị ghi hoặc gửi ra ngoài; cần kiểm tra cả `tool_results` và filesystem.

| Attack case | Expected boundary | Actual calls | Sensitive write/exfiltration occurred? | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Optional và bonus tool evidence

Phần này chỉ điền khi nhóm có sử dụng optional tool hoặc tự xây bonus tool.
Không làm phần này không ảnh hưởng việc hoàn thành core lab. `policy`,
`create_ticket` và `search_device_info` là tool có sẵn, không phải tool mới do
nhóm tự xây.

| Category | Evidence file | What worked | Risk / guardrail |
|---|---|---|---|
| Optional built-in |  |  |  |
| External search + privacy boundary |  |  |  |
| Bonus: tool mới do nhóm tự xây | `runs/v4_B_group_openai_20260914T191129935783.json` | `approved_software_catalog` pass 10/10 group cases | Tool read-only, dùng mock data, yêu cầu team và OS rõ; thiếu OS thì `clarify` |

## B6. Safety review

- Agent có bao giờ tự đoán asset ID hoặc employee ID không?
- Trace/ticket có chứa password, MFA code, token hay dữ liệu thật không?
- Ticket chỉ được tạo sau xác nhận rõ chưa?
- Tool result error nào cần review thủ công?

## B7. Technical reflection

- Fix nào thuộc `system_prompt.md`?
- Fix nào thuộc `tools.yaml`?
- Failure nào không thể chỉ nhìn automatic score?
- Nếu có thêm một vòng, nhóm sẽ thử hypothesis nào?

# PHẦN C — Checkout trước khi nộp

Phần này được hoàn thành sau khi toàn bộ code, evidence và report đã được đưa
lên repository chung. Nhóm chưa nên nộp link trên VLearn nếu reflection hoặc
commit evidence của bất kỳ thành viên nào còn thiếu.

## C1. Reflection chung của nhóm

Các thành viên thảo luận và viết một reflection chung. Nội dung cần dựa trên
evidence thực tế trong repository, không chỉ mô tả cảm nhận chung.

- Mục tiêu nào của nhóm đã hoàn thành? Dẫn đến artifact hoặc run tương ứng.
- Hypothesis hoặc thay đổi nào tạo ra cải thiện rõ nhất?
- Failure quan trọng nào vẫn chưa xử lý được hoàn toàn?
- Nhóm đã phân chia, review và tích hợp công việc như thế nào?
- Nếu có thêm một vòng, nhóm sẽ ưu tiên thay đổi và kiểm chứng điều gì?

**Reflection chung của nhóm:**

> Viết reflection tại đây và dẫn link/path đến evidence liên quan.

## C2. Self-reflection của từng thành viên

Mỗi thành viên tự viết một mục riêng về phần việc chính mình đã thực hiện trong
repository chung. Không viết thay hoặc gộp nhiều thành viên vào một câu trả lời.
Mỗi reflection cần trỏ đến file, commit hoặc pull request có thật để người đọc
có thể đối chiếu đóng góp.

Sao chép mẫu dưới đây cho từng thành viên:

### Họ tên — MSSV

- **Vai trò/phần việc được nhận:**
- **Những gì tôi đã thay đổi trong repo chung:**
- **File hoặc artifact liên quan:**
- **Commit hash hoặc pull request:**
- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:**
- **Khó khăn tôi gặp và cách tôi xử lý:**
- **Điều tôi học được từ phần việc này:**
- **Nếu làm lại, tôi sẽ cải thiện điều gì:**

Mỗi thành viên phải tự commit phần self-reflection của mình bằng Git identity
tương ứng. Reflection phải dẫn đến contribution artifact/commit đã nêu ở trên,
không dùng chính phần reflection làm bằng chứng duy nhất cho đóng góp kỹ thuật.

## C3. Final checkout

Chỉ nộp bài khi mọi mục dưới đây đã được kiểm tra trên branch cuối cùng của
repository chung:

- [ ] `TEAMMATES.md` có đủ họ tên, MSSV, GitHub username và vai trò.
- [ ] Mỗi thành viên có ít nhất một commit trong lịch sử branch nộp bài.
- [ ] Phần reflection chung của nhóm đã hoàn thành và có evidence.
- [ ] Mỗi thành viên đã tự viết và commit self-reflection của mình.
- [ ] `system_prompt.md`, `tools.yaml`, version log, runs, eval, transcript, UI
      và report đã có trong repository.
- [ ] Không có `.env`, API key, token, dữ liệu thật, cache hoặc generated ticket.
- [ ] Nhóm trưởng và mọi thành viên đã thống nhất đúng một URL repository chung.
- [ ] Nhóm trưởng và mọi thành viên sẽ nộp cùng URL đó trên VLearn.

**URL repository chung dùng để nộp:**

> URL:
