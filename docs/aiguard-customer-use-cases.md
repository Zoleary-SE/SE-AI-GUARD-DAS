# Zscaler AI Guard — customer use cases

Customer-facing use cases for two AI Guard designs: the business problem a customer would bring,
and what the design does about it.

## 1. AI Guard in DAS/API mode — customers building their own AI apps

The customer's application calls AI Guard to check each prompt and response.

| Customer situation | Use case |
|---|---|
| A bank launches a customer-service chatbot | Stop the bot being tricked by prompt injection into revealing other customers' account details |
| A healthcare provider builds a clinician assistant | Keep patient identifiers out of prompts sent to a third-party LLM |
| A retailer adds an AI shopping assistant to its website | Block toxic, off-brand or competitor-promoting answers before a shopper sees them |
| A software company ships an internal coding helper | Catch API keys and credentials pasted into prompts before they leave the company |
| A firm builds a document-search assistant over internal files | Scan retrieved content and answers so hidden instructions in a document can't hijack the assistant |
| A regulated business needs evidence for auditors | Log every prompt, verdict and detector per application to show AI controls are enforced |
| A platform team supports many AI projects | Give every team one shared guardrail service with a policy per app, instead of each team writing its own filters |

## 2. ZIA + AI Guard — customers whose employees use public AI tools

No app changes; employee traffic to tools like Claude is steered through AI Guard.

| Customer situation | Use case |
|---|---|
| Staff paste customer lists or contracts into Claude | Block sensitive data in the prompt before it reaches the AI provider |
| Leadership wants to allow AI tools, not ban them | Allow Claude for everyone, with guardrails, instead of blocking the site outright |
| Legal and finance handle more sensitive material | Apply stricter policies to those groups and lighter ones to everyone else |
| Security has no view of what employees ask AI tools | See who is using which AI app, with which policy and what was detected |
| Developers use AI coding assistants | Stop source code secrets and credentials being sent in prompts |
| The company has approved one AI tool and not others | Inspect the approved tool through AI Guard and use ZIA to block or caution on the rest |
| Compliance must show AI use is governed | Export AI Guard logs to the SIEM as evidence of enforced policy per user |

## Which one fits

- **Customer is building an AI app:** DAS/API mode, or app Proxy mode if they would sooner change a
  base URL than add API calls.
- **Customer's people are using someone else's AI app:** ZIA with AI Guard.
- **Many customers have both problems,** and the two designs run side by side.

These are illustrative scenarios written from what the two designs do, not documented Zscaler
customer stories.
