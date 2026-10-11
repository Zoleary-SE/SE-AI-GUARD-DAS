import streamlit as st
import json
import os
from openai import OpenAI
from zscaler.oneapi_client import LegacyAIGuardClient

CONFIG_PATH = "/config/config.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return None

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def scan_with_ai_guard(cfg, content, direction):
    try:
        client_config = {
            "api_key": cfg.get("aiguard_api_key"),
            "cloud": "us1",
        }
        with LegacyAIGuardClient(client_config) as client:
            result, _, err = client.aiguard.policy_detection.execute_policy(
                content=content,
                direction=direction,
                policy_id=cfg.get("aiguard_policy_id"),
            )
        if err:
            return None, str(err)
        return result.as_dict(), None
    except Exception as e:
        return None, str(e)

def evaluate_ai_guard(result, err):
    # Fail-closed: any error = not allowed, no detectors to report
    if err or result is None:
        return False, []
    allowed = result.get("action") == "ALLOW"
    triggered = [
        name for name, detector in (result.get("detector_responses") or {}).items()
        if isinstance(detector, dict) and detector.get("triggered")
    ]
    return allowed, triggered

def render_ai_guard_caption(allowed, triggered, err):
    if allowed:
        if triggered:
            st.caption(f"🛡️ AI Guard: Allowed (detected, not enforced: {', '.join(triggered)})")
        else:
            st.caption("🛡️ AI Guard: Allowed")
    else:
        detectors = ", ".join(triggered) if triggered else (err or "unknown")
        st.caption(f"🛡️ AI Guard: Blocked — {detectors}")

st.set_page_config(page_title="AI Guard Chat", page_icon="🛡️")

if "show_settings" not in st.session_state:
    st.session_state.show_settings = False
if "messages" not in st.session_state:
    st.session_state.messages = []

config = load_config()

def render_setup_form(existing):
    st.title("🛡️ AI Guard Chat — Setup")
    st.write("Enter your LLM and AI Guard details. Saved locally, only needs to be entered once.")

    with st.form("setup_form"):
        st.subheader("LLM")
        llm_base_url = st.text_input("API Base URL", value=existing.get("llm_base_url", "https://api.openai.com/v1"))
        llm_model = st.text_input("Model name", value=existing.get("llm_model", "gpt-5-nano"))
        llm_api_key = st.text_input("API Key", value=existing.get("llm_api_key", ""), type="password")

        st.subheader("Zscaler AI Guard")
        aiguard_api_key = st.text_input("AI Guard API Key", value=existing.get("aiguard_api_key", ""), type="password")
        aiguard_policy_id = st.text_input("AI Guard Policy ID", value=existing.get("aiguard_policy_id", ""))

        submitted = st.form_submit_button("Save")

    if submitted:
        new_config = {
            "llm_base_url": llm_base_url,
            "llm_model": llm_model,
            "llm_api_key": llm_api_key,
            "aiguard_api_key": aiguard_api_key,
            "aiguard_policy_id": aiguard_policy_id,
        }
        save_config(new_config)
        st.session_state.show_settings = False
        st.rerun()

def render_chat(cfg):
    st.title("🛡️ AI Guard Chat")
    with st.sidebar:
        st.write("Model:")
        st.code(cfg.get("llm_model", ""))
        if st.button("⚙️ Change settings"):
            st.session_state.show_settings = True
            st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Enter your prompt")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        prompt_result, prompt_err = scan_with_ai_guard(cfg, prompt, "IN")
        prompt_allowed, prompt_triggered = evaluate_ai_guard(prompt_result, prompt_err)
        render_ai_guard_caption(prompt_allowed, prompt_triggered, prompt_err)

        if not prompt_allowed:
            detectors = ", ".join(prompt_triggered) if prompt_triggered else (prompt_err or "unknown")
            reply = f"🛑 Blocked by AI Guard (prompt) — triggered: {detectors}"
            with st.chat_message("assistant"):
                st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.stop()

        client = OpenAI(base_url=cfg.get("llm_base_url"), api_key=cfg.get("llm_api_key"))

        with st.chat_message("assistant"):
            with st.spinner("Waiting on LLM response..."):
                llm_reply, llm_error = None, None
                try:
                    response = client.chat.completions.create(
                        model=cfg.get("llm_model"),
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    )
                    llm_reply = response.choices[0].message.content
                except Exception as e:
                    llm_error = str(e)

            if llm_error:
                reply = f"Error calling LLM: {llm_error}"
            else:
                response_result, response_err = scan_with_ai_guard(cfg, llm_reply, "OUT")
                response_allowed, response_triggered = evaluate_ai_guard(response_result, response_err)
                render_ai_guard_caption(response_allowed, response_triggered, response_err)

                if response_allowed:
                    reply = llm_reply
                else:
                    detectors = ", ".join(response_triggered) if response_triggered else (response_err or "unknown")
                    reply = f"🛑 Blocked by AI Guard (response) — triggered: {detectors}"

            st.write(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

if config is None or st.session_state.show_settings:
    render_setup_form(config or {})
else:
    render_chat(config)
