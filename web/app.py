"""FanDraGen web UI (Streamlit). Run from repo root: make run"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import streamlit as st

from utils.env import gemini_api_key, live_espn_enabled, load_env
from utils.file_utils import read_yaml
from utils.logging_utils import summarize_logs
from utils.trace_utils import build_trace_snapshot
from workflows.orchestrator import WorkflowOrchestrator


def _load_demo_config() -> dict:
    return read_yaml(ROOT / "configs" / "default_config.yaml")


def _run_workflow(query: str):
    load_env()
    return WorkflowOrchestrator().run(query)


def main() -> None:
    st.set_page_config(
        page_title="FanDraGen",
        page_icon="🏀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
<style>
    .stApp {
        background: linear-gradient(165deg, #0c1220 0%, #111827 45%, #0f172a 100%);
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0b1220 100%);
        border-right: 1px solid rgba(249,115,22,0.25);
    }
    h1 { color: #f8fafc !important; letter-spacing: -0.02em; }
    .tagline { color: #94a3b8; font-size: 1.05rem; margin-top: -0.5rem; }
    .pill { display: inline-block; padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.8rem;
            margin-right: 0.35rem; margin-bottom: 0.35rem; border: 1px solid rgba(148,163,184,0.35); color: #e2e8f0; }
    .pill-on { border-color: rgba(34,197,94,0.55); background: rgba(34,197,94,0.12); }
    .pill-off { border-color: rgba(148,163,184,0.35); background: rgba(30,41,59,0.5); }
</style>
        """,
        unsafe_allow_html=True,
    )

    cfg = _load_demo_config()
    demo = cfg.get("demo", {})
    prompts: list[str] = demo.get("prompts", [])
    default_idx = int(demo.get("default_prompt_index", 0))

    st.markdown("# FanDraGen")
    st.markdown(
        '<p class="tagline">NBA fantasy co-pilot — routing, boss orchestration, tools, evaluators, approval gates.</p>',
        unsafe_allow_html=True,
    )

    load_env()
    gemini_on = bool(gemini_api_key())
    espn_on = live_espn_enabled()

    with st.sidebar:
        st.markdown("### Session")
        st.markdown(
            f'<span class="pill pill-on">Demo data</span>'
            f'<span class="pill {"pill-on" if gemini_on else "pill-off"}">Gemini: {"on" if gemini_on else "off"}</span>'
            f'<span class="pill {"pill-on" if espn_on else "pill-off"}">ESPN live: {"on" if espn_on else "off"}</span>',
            unsafe_allow_html=True,
        )
        st.caption("Configure `.env`: `GEMINI_API_KEY`, optionally `FANDRAGEN_LIVE_ESPN=1`.")

        st.markdown("### Scenario")
        st.caption(str(demo.get("scenario_name", "")))
        st.caption(str(demo.get("calendar_window", "")))

        st.markdown("### Quick prompts")
        for i, p in enumerate(prompts):
            label = p if len(p) <= 56 else p[:53] + "…"
            if st.button(label, key=f"qp_{i}", use_container_width=True):
                with st.spinner("Running…"):
                    try:
                        st.session_state["last_state"] = _run_workflow(p)
                        st.session_state["main_query"] = p
                    except Exception as e:
                        st.session_state["last_error"] = str(e)
                        st.session_state["last_state"] = None

    if "main_query" not in st.session_state:
        st.session_state["main_query"] = prompts[default_idx] if prompts else ""

    query = st.text_area(
        "Your prompt",
        height=120,
        placeholder="Ask about waivers, lineups, trades, news…",
        label_visibility="collapsed",
        key="main_query",
    )

    if st.button("Run FanDraGen", type="primary"):
        st.session_state.pop("last_error", None)
        with st.spinner("Running orchestrator…"):
            try:
                q = (query or "").strip() or (prompts[0] if prompts else "Hello")
                st.session_state["last_state"] = _run_workflow(q)
                st.session_state["main_query"] = q
            except Exception as e:
                st.session_state["last_error"] = str(e)
                st.session_state["last_state"] = None

    if "last_error" in st.session_state and st.session_state["last_error"]:
        st.error(st.session_state["last_error"])

    state = st.session_state.get("last_state")
    if state is None:
        st.info("Run a **quick prompt** from the sidebar or edit the text box and click **Run FanDraGen**.")
        return

    final = state.final_delivery_payload
    trace = build_trace_snapshot(state)

    tab1, tab2, tab3 = st.tabs(["Answer", "Trace & metrics", "Raw JSON"])

    with tab1:
        if final:
            st.markdown(final.markdown_summary)
        else:
            st.warning("No delivery payload.")

    with tab2:
        st.subheader("Trace snapshot")
        st.json(trace)
        st.subheader("Log summary")
        st.code(summarize_logs(state), language=None)
        st.subheader("Workflow metrics")
        st.json(dict(state.metrics))

    with tab3:
        if final:
            st.json(final.json_payload)
        else:
            st.json({"error": "no final payload"})

    fd = final.json_payload.get("fallback_demo_data_usage", {}) if final else {}
    if fd.get("gemini_enrichment_applied"):
        st.success("Gemini polish was applied (see `gemini_enrichment_applied` in Raw JSON).")


if __name__ == "__main__":
    main()
