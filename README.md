# ByMeSaved

A self-hosted Telegram knowledge manager for saving messages and finding them later. It combines full-text and semantic search, AI-generated metadata, retrieval-augmented answers, and Markdown export for Obsidian.

## Stack

- Python 3.12 and aiogram 3
- PostgreSQL 16 with pgvector
- OpenRouter chat and embedding models
- Docker Compose

## Run locally

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather).
2. Copy `.env.example` to `.env` and configure the required values.
3. Start the services:

```sh
docker compose up -d --build
docker compose logs -f bot
```

Keep API keys and the Telegram token in `.env`; do not commit them. Any key that has appeared in a commit or public log should be revoked and replaced. A previously exposed OpenRouter key must be treated as compromised.

## Project status

This repository documents a personal project. Model availability, provider pricing, and free-tier limits may change; configure the providers and models available to your deployment.
