# AI Guard Chat — design and AI Guard interaction

Source: [`Zoleary-SE/SE-AI-GUARD-DAS`](https://github.com/Zoleary-SE/SE-AI-GUARD-DAS) (`app.py`, `requirements.txt`).
Docker image: `tomzscaler/aiguard-chat:latest` on Docker Hub (amd64 and arm64).

The app is a single 161-line Streamlit app that puts Zscaler AI Guard in front of and behind an LLM call.

## Design

```
                           ┌──────────────────────────────────────────────┐
                           │  Container: aiguard-chat  (python 3.12)      │
                           │  streamlit run app.py   → port 8080          │
┌───────────┐   HTTP :8080 │                                              │
│  Browser  │◄────────────►│  ┌──────────────┐      ┌──────────────────┐  │
│  (user)   │              │  │ Setup form   │─────►│ /config/         │  │
└───────────┘              │  │ (first run / │ save │   config.json    │  │
                           │  │  ⚙ settings) │◄─────│ LLM URL, model,  │  │
                           │  └──────────────┘ load │ LLM key, AI Guard│  │
                           │                        │ key + policy ID  │  │
                           │  ┌──────────────┐      └──────────────────┘  │
                           │  │ Chat page    │                            │
                           │  │ + session    │                            │
                           │  │   history    │                            │
                           │  └──┬────────┬──┘                            │
                           └─────┼────────┼───────────────────────────────┘
                                 │        │
              zscaler-sdk-python │        │ openai client
              execute_policy()   │        │ chat.completions
                                 ▼        ▼
                    ┌─────────────────┐  ┌──────────────────────────┐
                    │ Zscaler AI Guard│  │ LLM (OpenAI-compatible)  │
                    │ cloud "us1"     │  │ default: OpenAI,         │
                    │ DAS/API mode    │  │ gpt-5-nano               │
                    └─────────────────┘  └──────────────────────────┘
```

Components:

| Piece | What it is |
|---|---|
| Container | `python:3.12` base, `streamlit run app.py` on port 8080 |
| Dependencies | `streamlit`, `openai`, `zscaler-sdk-python>=1.9.44` |
| Setup form | Shown on first run or from "Change settings"; collects LLM base URL, model, LLM key, AI Guard key, AI Guard policy ID |
| Config | `/config/config.json`, plain-text JSON, one config for all visitors |
| Chat history | Streamlit session state, per browser session, not persisted |
| AI Guard client | `LegacyAIGuardClient` → `aiguard.policy_detection.execute_policy`, cloud hard-coded to `us1` |
| LLM client | `openai` SDK against any OpenAI-compatible endpoint (default OpenAI, `gpt-5-nano`) |

## How AI Guard interacts

The app calls AI Guard twice per turn, as an out-of-band check. AI Guard never sits in the
network path to the LLM; it only returns a verdict that the app enforces.

```
 User            App (app.py)                 AI Guard                LLM
  │  prompt        │                             │                     │
  ├───────────────►│                             │                     │
  │                │ ① execute_policy(prompt,    │                     │
  │                │    direction="IN",          │                     │
  │                │    policy_id)               │                     │
  │                ├────────────────────────────►│                     │
  │                │◄──── action + detectors ────┤                     │
  │                │                             │                     │
  │                │── not ALLOW ──► "🛑 Blocked (prompt) — <detectors>"
  │◄───────────────┤                 stop; LLM is never called         │
  │                │                             │                     │
  │                │── ALLOW ──► ② send full chat history              │
  │                ├──────────────────────────────────────────────────►│
  │                │◄────────────────────── reply ─────────────────────┤
  │                │                             │                     │
  │                │ ③ execute_policy(reply,     │                     │
  │                │    direction="OUT",         │                     │
  │                │    policy_id)               │                     │
  │                ├────────────────────────────►│                     │
  │                │◄──── action + detectors ────┤                     │
  │                │                             │                     │
  │  reply, or     │── ALLOW ──► show LLM reply  │                     │
  │  "🛑 Blocked   │── not ALLOW ──► show block message instead        │
  │◄───────────────┤                             │                     │
```

- **Verdict:** only `action == "ALLOW"` passes. The app lists every detector marked `triggered` in the response.
- **Fail closed:** any AI Guard error or timeout counts as blocked, with the error text shown as the reason.
- **Detect-only:** if AI Guard allows but detectors fired, the caption reads "Allowed (detected, not enforced: …)".
- **Authentication:** one AI Guard API key plus a policy ID, both typed into the setup form.

## Things worth knowing before lab day

- **Blocked prompts still reach the LLM later.** A blocked prompt is saved to the chat history before
  the scan, and step ② sends the whole history. The next allowed prompt carries the blocked one along
  with it, unscanned.
- **Keys are stored in plain text** in `/config/config.json`, and anyone who can open the page can open
  the settings form.
- **The config is shared; the history is not.** One saved config serves every visitor, while chat
  history is per browser session.
- **No system prompt.** The LLM gets only the conversation, so there is no built-in "secret" for
  attendees to extract.
- **Inferred, not confirmed:** the image was built with Docker Compose, but the compose file is not in
  the image, so the `/config` volume mapping is inferred from the code.
