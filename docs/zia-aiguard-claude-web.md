# ZIA + Zscaler AI Guard — user traffic to Claude on the web

How a user's browser session to `claude.ai` is steered through Zscaler Internet Access (ZIA) to
AI Guard for prompt and response inspection.

**A note on the name.** In the AI Guard docs, "Proxy mode" means an *application* sending its LLM API
calls to AI Guard as a reverse proxy (`proxy.zseclipse.net`). A *user* browsing to Claude is a
different path: ZIA **proxy-chains** the traffic to AI Guard. This document covers the ZIA
proxy-chain path, because that is the one that applies to Claude on the web.

## Network diagram

```
┌────────────────────────────┐
│ User device                │
│  Browser → claude.ai       │
│  Zscaler Client Connector  │
│  (or site GRE/IPsec, PAC)  │
└─────────────┬──────────────┘
              │ tunnel: user's web traffic
              ▼
┌──────────────────────────────────────────────┐         ┌──────────────┐
│ ZIA Public Service Edge                      │◄───────►│ Identity     │
│  • user signed in to ZIA                     │  login  │ provider     │
│  • Firewall rule: block QUIC                 │         └──────────────┘
│  • Forwarding Control rule:                  │
│      *.claude.ai, *.api.anthropic.com        │
│      → Proxy Chaining                        │
│  • Proxy gateway → AI Guard, Fail Close      │
└─────────────┬─────────────────────┬──────────┘
              │ matched AI traffic  │ everything else
              │ TLS to port 9443    ▼
              │ X-Authenticated-    Internet, straight from ZIA
              │ User header         (normal ZIA policy)
              ▼
┌──────────────────────────────────────────────┐
│ Zscaler AI Guard                             │
│  forward.zseclipse.net : 9443                │
│  • user → Policy Match (user or group)       │
│  • detectors on prompt and on response       │
│  • allow, or block with a block message      │
│  • logs to the Users dashboard / exports     │
└─────────────┬────────────────────────────────┘
              │ allowed requests only
              ▼
┌──────────────────────────────────────────────┐
│ Anthropic — claude.ai (web app)              │
└──────────────────────────────────────────────┘
```

## Flow

```
 Browser             ZIA service edge        AI Guard             claude.ai
   │                  │                      │                     │
   │ 1 HTTPS request  │                      │                     │
   │   to claude.ai   │                      │                     │
   ├─────────────────►│                      │                     │
   │                  │ 2 authenticate user, │                     │
   │                  │   block QUIC, match  │                     │
   │                  │   Forwarding Control │                     │
   │                  │   rule (*.claude.ai) │                     │
   │                  │                      │                     │
   │                  │ 3 proxy-chain to     │                     │
   │                  │   :9443 with         │                     │
   │                  │   X-Authenticated-   │                     │
   │                  │   User header        │                     │
   │                  ├─────────────────────►│                     │
   │                  │                      │ 4 map user to a     │
   │                  │                      │   policy, run       │
   │                  │                      │   prompt detectors  │
   │                  │                      │                     │
   │                  │◄── block message ────┤ if blocked: stop,   │
   │◄─────────────────┤                      │ nothing is sent on  │
   │                  │                      │                     │
   │                  │                      │ 5 if allowed:       │
   │                  │                      │   forward request   │
   │                  │                      ├────────────────────►│
   │                  │                      │◄───── response ─────┤
   │                  │                      │                     │
   │                  │                      │ 6 run response      │
   │                  │                      │   detectors         │
   │                  │◄─ response, or block ┤                     │
   │◄─────────────────┤                      │                     │
   │                  │                      │                     │
   │                  │ 7 ZIA web logs       │ 7 AI Guard Users    │
   │                  │                      │   dashboard, exports│
```

1. The user opens `claude.ai` and sends a prompt. The traffic reaches ZIA through Client Connector
   or a site tunnel.
2. ZIA identifies the signed-in user. QUIC is blocked, so the browser falls back to TCP/TLS, which
   ZIA can forward. The Forwarding Control rule matches the Claude domains.
3. ZIA proxy-chains the request to the AI Guard proxy gateway, adding the user's identity in the
   `X-Authenticated-User` header.
4. AI Guard matches the user to a policy and runs the prompt detectors. If the policy blocks, the
   request stops here and a block message goes back.
5. If allowed, AI Guard forwards the request to Claude.
6. AI Guard runs the response detectors and returns the response, or a block.
7. ZIA logs the web transaction; AI Guard logs the user, policy, detections and action.

**Fail Close** means that if AI Guard is unreachable, the Claude traffic is dropped, not sent direct.

## What has to be configured

| Where | Setting |
|---|---|
| Zscaler Support | ZIA and AI Guard tenants linked; one AI Guard tenant per domain; Experience Center enabled |
| ZIA › Root Certificates | Upload the AI Guard CA certificate, type **Proxy Chaining** |
| ZIA › Proxies and Gateways | Proxy `forward.zseclipse.net`, port `9443`, AI Guard root certificate, **Insert X-Authenticated-User** on, Base64 encoding of that header off |
| ZIA › Proxies and Gateways | Proxy gateway with the AI Guard proxy as primary, **Fail Close** |
| ZIA › Firewall Filtering | Rule to block QUIC |
| ZIA › Forwarding Control | Wildcard FQDN group with `*.claude.ai` and `*.api.anthropic.com`; rule using **Proxy Chaining** to the gateway |
| AI Guard › Policy Control | Policy Match for users or groups (default `AllUsersGroup`); detectors enabled on prompts and responses |

## How sure this is

- **Documented:** the prerequisites, the ZIA settings in the table, the Claude domains, and that ZIA
  users appear in AI Guard automatically (groups do not). These come from Zscaler's help article
  "Integrating ZIA with AI Guard", read from a third-party capture dated 2026-09-03; its
  supported-app table was marked last updated 2026-09-02. The live help page would not load for
  me, so check it and your tenant before building.
- **Inferred, not documented in what I read:** the step-by-step order in the flow; where the TLS
  session to Claude is decrypted (ZIA SSL inspection, AI Guard, or both); and how a block appears
  inside the Claude web page.
- **Not covered:** which Claude clients are supported (browser, desktop app, Claude Code). The help
  page has a client-type column that the capture left out.
- **Licensing:** this needs an AI Guard subscription on top of ZIA.

Sources: https://help.zscaler.com/secure-ai-users/integrating-zia-ai-guard ·
https://github.com/dvmrry/zscaler-skill (capture of that page) ·
https://help.zscaler.com/secure-ai-users/test-llm-providers-ai-guard-proxy-mode
