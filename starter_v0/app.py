from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
VERSION_PROMPTS = {
    "v1": ARTIFACTS_DIR / "system_prompt_v1.md",
    "v2": ARTIFACTS_DIR / "system_prompt_v2.md",
    "v3": ARTIFACTS_DIR / "system_prompt_v3.md",
    "v4": ARTIFACTS_DIR / "system_prompt_v4.md",
}
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
DEMO_PROMPTS = {
    "Core multi-tool": "VPN trên LT-204 lỗi; kiểm tra cả trạng thái VPN production và máy đó.",
    "Missing asset": "Kiểm tra Wi-Fi trên laptop của mình giúp nhé.",
    "Ticket boundary": "Tạo ticket mức high cho lỗi VPN trên LT-204 giúp mình.",
    "Bonus catalog": "Phần mềm VPN nào được duyệt cho team Engineering trên macOS?",
}


def json_block(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


@st.cache_data(show_spinner=False)
def load_artifacts(version: str) -> dict[str, Any]:
    prompt_path = VERSION_PROMPTS[version]
    prompt = prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(TOOLS_PATH)
    tools = to_openai_tools(declarations)
    artifact_version = build_artifact_version(version, prompt_path, TOOLS_PATH)
    return {
        "prompt": prompt,
        "prompt_path": str(prompt_path),
        "tools": tools,
        "artifact_version": artifact_version_dict(artifact_version),
    }


@st.cache_resource(show_spinner=False)
def provider_for(name: str) -> Any:
    return make_provider(name)


def new_transcript(version: str, provider_name: str, model: str | None, artifacts: dict[str, Any]) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), timestamp])
    return {
        "transcript_id": transcript_id,
        **artifacts["artifact_version"],
        "provider": provider_name,
        "model": model,
        "system_prompt": artifacts["prompt_path"],
        "tools": str(TOOLS_PATH),
        "history_window": st.session_state.history_window,
        "max_tool_rounds": st.session_state.max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def transcript_path() -> Path:
    return TRANSCRIPTS_DIR / f"{st.session_state.transcript['transcript_id']}.transcript.json"


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.turns = []
    st.session_state.transcript = None


def ensure_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("turns", [])
    st.session_state.setdefault("transcript", None)
    st.session_state.setdefault("pending_prompt", "")
    st.session_state.setdefault("history_window", 5)
    st.session_state.setdefault("max_tool_rounds", 4)


def render_turn_details(turn: dict[str, Any]) -> None:
    status = turn.get("status", "unknown")
    st.caption(f"Status: `{status}`")
    for round_record in turn.get("rounds", []):
        label = f"Round {round_record.get('round')}"
        calls = round_record.get("tool_calls") or []
        if calls:
            label += f" - {', '.join(call.get('name', 'tool') for call in calls)}"
        with st.expander(label, expanded=bool(calls)):
            assistant_text = round_record.get("assistant_text")
            if assistant_text:
                st.markdown(assistant_text)
            st.markdown("Tool calls")
            st.code(json_block(calls), language="json")
            st.markdown("Tool results")
            st.code(json_block(round_record.get("tool_results", [])), language="json")


def run_turn(user_text: str, *, version: str, provider_name: str, model: str | None, artifacts: dict[str, Any]) -> None:
    provider = provider_for(provider_name)
    selected_model = model or getattr(provider, "default_model", None)
    if st.session_state.transcript is None:
        st.session_state.transcript = new_transcript(version, provider_name, selected_model, artifacts)

    messages = [
        {"role": "system", "content": artifacts["prompt"]},
        *trim_history(st.session_state.messages, st.session_state.history_window),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=artifacts["tools"],
            model=model or None,
            max_tool_rounds=st.session_state.max_tool_rounds,
        )
        turn_record.update(result)
        assistant_text = result["assistant_text"]
    except Exception as exc:
        assistant_text = f"{type(exc).__name__}: {exc}"
        turn_record.update({
            "status": "provider_error",
            "assistant_text": assistant_text,
            "error": assistant_text,
        })

    turn_record["ended_at"] = now_iso()
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    st.session_state.turns.append(turn_record)
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(transcript_path(), st.session_state.transcript)


def main() -> None:
    st.set_page_config(page_title="Northstar IT Helpdesk", page_icon=":material/support_agent:", layout="wide")
    ensure_state()

    with st.sidebar:
        st.title("Northstar IT")
        provider_name = st.selectbox("Provider", ["openai", "openrouter", "anthropic", "gemini"], index=0)
        version = st.selectbox("Prompt version", list(VERSION_PROMPTS), index=3)
        model = st.text_input("Model override", value="", placeholder="default provider model").strip() or None
        st.session_state.history_window = st.slider("History window", 1, 10, st.session_state.history_window)
        st.session_state.max_tool_rounds = st.slider("Max tool rounds", 1, 8, st.session_state.max_tool_rounds)

        if st.button("New transcript", use_container_width=True):
            reset_chat()
            st.rerun()

        st.divider()
        selected_demo = st.selectbox("Demo prompt", list(DEMO_PROMPTS))
        if st.button("Use demo prompt", use_container_width=True):
            st.session_state.pending_prompt = DEMO_PROMPTS[selected_demo]
            st.rerun()

    artifacts = load_artifacts(version)
    artifact_version = artifacts["artifact_version"]

    st.title("IT Helpdesk Agent")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Version", artifact_version["version"])
    metric_cols[1].metric("Provider", provider_name)
    metric_cols[2].metric("Prompt hash", artifact_version["prompt_hash"][:12])
    metric_cols[3].metric("Tools hash", artifact_version["tools_hash"][:12])
    st.caption(f"Artifact: `{artifact_version['artifact_version']}`")

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                turn_index = index // 2
                if turn_index < len(st.session_state.turns):
                    render_turn_details(st.session_state.turns[turn_index])

    user_text = st.session_state.pending_prompt or st.chat_input("Nhập yêu cầu helpdesk")
    if st.session_state.pending_prompt:
        st.session_state.pending_prompt = ""

    if user_text:
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.spinner("Agent đang xử lý..."):
            run_turn(user_text, version=version, provider_name=provider_name, model=model, artifacts=artifacts)
        st.rerun()

    if st.session_state.transcript:
        path = transcript_path()
        st.sidebar.divider()
        st.sidebar.caption(f"Transcript: `{path}`")
        st.sidebar.download_button(
            "Download transcript",
            data=path.read_text(encoding="utf-8") if path.exists() else json_block(st.session_state.transcript),
            file_name=path.name,
            mime="application/json",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
