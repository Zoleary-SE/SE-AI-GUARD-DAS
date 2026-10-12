# SE-AI-GUARD-DAS

Streamlit chat app that checks every prompt and LLM response with Zscaler AI Guard (DAS/API mode).
Docker image: [`tomzscaler/aiguard-chat`](https://hub.docker.com/r/tomzscaler/aiguard-chat) (amd64 and arm64).

## Run the prebuilt image

    docker run -d -p 8080:8080 -v ./config:/config tomzscaler/aiguard-chat:latest

Published on Docker Hub for amd64 and arm64.

## Build from source

    git clone https://github.com/Zoleary-SE/SE-AI-GUARD-DAS.git
    cd SE-AI-GUARD-DAS
    docker compose up -d --build

Open http://localhost:8080 (set `PORT=8081` before the command if 8080 is taken; it listens on all
interfaces, and the app has no login, so set `BIND=127.0.0.1` on an untrusted network) and enter the LLM and AI Guard details
(defaults: OpenAI `https://api.openai.com/v1`, model `gpt-5-nano`). They are saved in plain text to
`./config/config.json`, which is git-ignored.

Design notes are in `docs/`.
