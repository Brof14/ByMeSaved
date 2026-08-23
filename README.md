# Personal Knowledge Bot

Lightweight Telegram knowledge manager: save forwarded/text messages, AI metadata + embeddings, semantic/full-text search, RAG answers and Obsidian Markdown export.

## Stack
- Python 3.12
- aiogram 3
- PostgreSQL 16 + pgvector
- OpenRouter chat model
- OpenRouter free Nemotron embedding model
- Docker Compose

## Security
Put secrets only into `.env`. Never commit them.

## Start

1. Create a Telegram bot and get `BOT_TOKEN`.
2. Revoke any previously exposed OpenRouter key and create a new one.
3. Copy `.env.example` to `.env` and fill values.
4. `docker compose up -d --build`
5. `docker compose logs -f bot`
