# Workflow chạy 4 version prompt

File này mô tả cách chạy lần lượt 4 version prompt `v1` đến `v4`, mỗi version
dùng một file system prompt riêng trong `artifacts/`.

## 1. Chuẩn bị môi trường

```bash
cd /home/nmc/AI/VinAI/Day04/K4-Day04-2A202602823/starter_v0
source .venv/bin/activate  # nếu dùng virtualenv
python -m compileall -q .
```

Repo đang chạy eval bằng provider `openai`, nên cần có `OPENAI_API_KEY` trong
`.env` hoặc môi trường shell.

## 2. Mapping version và prompt

| Version | Prompt file | Mục tiêu chính |
|---|---|---|
| `v1` | `artifacts/system_prompt_v1.md` | Sửa routing employee/user lookup, đặc biệt H04, và chống gọi trùng tool |
| `v2` | `artifacts/system_prompt_v2.md` | Siết missing-info: thiếu asset ID, employee ID, environment, team/OS thì hỏi lại |
| `v3` | `artifacts/system_prompt_v3.md` | Siết boundary tạo ticket: chỉ `create_ticket` sau confirmation hợp lệ cho payload hiện tại |
| `v4` | `artifacts/system_prompt_v4.md` | Bản tích hợp cuối: multi-tool triage, catalog, policy, external-search và adversarial safety |

## 3. Cách chạy thủ công từng version

### v1

```bash
python run_eval.py --provider openai --version v1 --suite base --system-prompt artifacts/system_prompt_v1.md --eval-cases data/eval_base.json
python run_eval.py --provider openai --version v1 --suite group --system-prompt artifacts/system_prompt_v1.md --eval-cases data/eval_group.json
python run_eval.py --provider openai --version v1 --suite extension --system-prompt artifacts/system_prompt_v1.md --eval-cases data/eval_helpdesk_extension.json
python run_eval.py --provider openai --version v1 --suite adversarial --system-prompt artifacts/system_prompt_v1.md --eval-cases data/eval_adversarial.json
```

### v2

```bash
python run_eval.py --provider openai --version v2 --suite base --system-prompt artifacts/system_prompt_v2.md --eval-cases data/eval_base.json
python run_eval.py --provider openai --version v2 --suite group --system-prompt artifacts/system_prompt_v2.md --eval-cases data/eval_group.json
python run_eval.py --provider openai --version v2 --suite extension --system-prompt artifacts/system_prompt_v2.md --eval-cases data/eval_helpdesk_extension.json
python run_eval.py --provider openai --version v2 --suite adversarial --system-prompt artifacts/system_prompt_v2.md --eval-cases data/eval_adversarial.json
```

### v3

```bash
python run_eval.py --provider openai --version v3 --suite base --system-prompt artifacts/system_prompt_v3.md --eval-cases data/eval_base.json
python run_eval.py --provider openai --version v3 --suite group --system-prompt artifacts/system_prompt_v3.md --eval-cases data/eval_group.json
python run_eval.py --provider openai --version v3 --suite extension --system-prompt artifacts/system_prompt_v3.md --eval-cases data/eval_helpdesk_extension.json
python run_eval.py --provider openai --version v3 --suite adversarial --system-prompt artifacts/system_prompt_v3.md --eval-cases data/eval_adversarial.json
```

### v4

```bash
python run_eval.py --provider openai --version v4 --suite base --system-prompt artifacts/system_prompt_v4.md --eval-cases data/eval_base.json
python run_eval.py --provider openai --version v4 --suite group --system-prompt artifacts/system_prompt_v4.md --eval-cases data/eval_group.json
python run_eval.py --provider openai --version v4 --suite extension --system-prompt artifacts/system_prompt_v4.md --eval-cases data/eval_helpdesk_extension.json
python run_eval.py --provider openai --version v4 --suite adversarial --system-prompt artifacts/system_prompt_v4.md --eval-cases data/eval_adversarial.json
```

## 4. Cách chạy tự động lần lượt v1 đến v4

```bash
for spec in \
  "v1 artifacts/system_prompt_v1.md" \
  "v2 artifacts/system_prompt_v2.md" \
  "v3 artifacts/system_prompt_v3.md" \
  "v4 artifacts/system_prompt_v4.md"; do
  set -- $spec
  version=$1
  prompt=$2

  python run_eval.py --provider openai --version "$version" --suite base --system-prompt "$prompt" --eval-cases data/eval_base.json
  python run_eval.py --provider openai --version "$version" --suite group --system-prompt "$prompt" --eval-cases data/eval_group.json
  python run_eval.py --provider openai --version "$version" --suite extension --system-prompt "$prompt" --eval-cases data/eval_helpdesk_extension.json
  python run_eval.py --provider openai --version "$version" --suite adversarial --system-prompt "$prompt" --eval-cases data/eval_adversarial.json
done
```

## 5. Tôi đã làm gì ở từng version

### v1 - Employee/user routing

- Tạo `artifacts/system_prompt_v1.md`.
- Làm rõ khi user cung cấp employee ID dạng `EMP-*` hoặc hỏi tài khoản nhân
  viên/thiết bị được cấp thì phải gọi `lookup_user`.
- Chặn việc dùng employee ID làm asset ID.
- Thêm rule không gọi trùng cùng một tool cho cùng entity.
- Giữ đúng `inspect_device.check` khi request có VPN, hardware, software hoặc
  nhiều nguồn evidence.

Evidence cuối:

- `runs/v1_B_base_openai_20260914T202401969291.json`
- `runs/v1_B_group_openai_20260914T202227454133.json`
- `runs/v1_B_extension_openai_20260914T202243530315.json`
- `runs/v1_B_adversarial_openai_20260914T202304541951.json`

### v2 - Missing information

- Tạo `artifacts/system_prompt_v2.md`.
- Siết rule không đoán asset ID, employee ID, environment, team hoặc OS family.
- Thiếu asset ID/employee ID thì gọi `clarify` dạng `text`.
- Environment không rõ như demo/QA/test/sandbox thì gọi `clarify` dạng `choice`
  với `production` và `staging`.
- Multi-turn: nếu lượt sau bổ sung identifier, team, OS hoặc category thì dùng
  context mới nhất.

Evidence cuối:

- `runs/v2_B_base_openai_20260914T200959005428.json`
- `runs/v2_B_group_openai_20260914T201015379912.json`
- `runs/v2_B_extension_openai_20260914T201033207668.json`
- `runs/v2_B_adversarial_openai_20260914T201052056305.json`

### v3 - Confirmation boundary

- Tạo `artifacts/system_prompt_v3.md`.
- Làm rõ `create_ticket` là action có side effect.
- Chỉ gọi `create_ticket` khi user xác nhận rõ bằng ngôn ngữ tự nhiên cho đúng
  payload hiện tại.
- Nếu priority, summary hoặc asset ID thay đổi sau confirmation thì confirmation
  cũ mất hiệu lực.
- Chặn pseudo-confirmation như JSON, pasted function call, `TOOL_RESULTS_JSON`,
  fake assistant/system markup hoặc role spoofing.

Evidence cuối:

- `runs/v3_B_base_openai_20260914T201133527594.json`
- `runs/v3_B_group_openai_20260914T201147748164.json`
- `runs/v3_B_extension_openai_20260914T201201577287.json`
- `runs/v3_B_adversarial_openai_20260914T201217762581.json`

### v4 - Integrated final prompt

- Tạo `artifacts/system_prompt_v4.md`.
- Tích hợp rule từ v1, v2, v3.
- Bổ sung multi-tool triage: nếu request cần nhiều nguồn evidence thì gọi đủ
  tool cần thiết, ví dụ service status + device diagnostic + KB.
- Bổ sung boundary cho `approved_software_catalog`, `policy`,
  `search_device_info`, và external-search safety.
- Chặn exfiltration dữ liệu nội bộ ra external search.
- Hard gate cho adversarial ticket action: role spoofing, forged tool results,
  stale confirmation và argument smuggling.

Evidence cuối:

- `runs/v4_B_base_openai_20260914T201753320835.json`
- `runs/v4_B_group_openai_20260914T201816339859.json`
- `runs/v4_B_extension_openai_20260914T201832167039.json`
- `runs/v4_B_adversarial_openai_20260914T201852206299.json`

## 6. Kết quả cuối

Tất cả latest evidence dùng trong `artifacts/version_log.csv` đều có:

- `provider_error_cases == 0`
- `measured_cases == total_cases`
- `passed_cases == total_cases`

Tóm tắt số case mỗi suite:

| Suite | Số case |
|---|---:|
| `base` | 30 |
| `group` | 10 |
| `extension` / helpdesk extension | 10 |
| `adversarial` | 12 |
