# Telegram real-time scraper service

This repository provides a small service that listens to Telegram channels or groups and forwards each new message to an [n8n](https://n8n.io) webhook. It is based on [Telethon](https://github.com/LonamiWebs/Telethon) and is designed for continuous operation on a server or VPS.

## Requirements

- Docker + docker compose **or** Python 3.11
- Telegram API credentials (api id/hash and a phone number)
- n8n instance with an incoming webhook

## Configuration

All configuration is done via a `.env` file. Copy the example and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `TG_API_ID` | Telegram API ID |
| `TG_API_HASH` | Telegram API hash |
| `TG_PHONE` | Phone number in international format |
| `TG_USERNAME` | Session name without `@` |
| `TG_CHANNELS` | Comma separated list of channels, e.g. `@group1,@group2` |
| `N8N_WEBHOOK_URL` | Full URL of n8n webhook |
| `HTTP_TIMEOUT` | HTTP request timeout in seconds |
| `HTTP_MAX_RETRIES` | Max retries for webhook requests |
| `HTTP_BACKOFF_SECONDS` | Base backoff between retries |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, etc.) |
| `STATE_BACKEND` | Currently only `file` is implemented |
| `STATE_FILE` | Path to JSON file storing last message IDs |

## Авторизація в Telegram

Перед запуском сервісу потрібно один раз згенерувати session-файл для Telethon:

1. Скопіюйте `.env.example` в `.env` та вкажіть значення `TG_API_ID`, `TG_API_HASH` і `TG_USERNAME=anon`.
2. Запустіть локально (поза Docker):

   ```bash
   python scripts/create_session.py
   ```

   Після введення коду підтвердження в каталозі `sessions/` з'явиться файл `anon.session`.
3. Переконайтеся, що `anon.session` знаходиться в директорії `sessions/` репозиторію.
4. Запустіть контейнер:

   ```bash
   docker compose up -d
   ```

Скрипт `scripts/create_session.py` потрібно запускати лише один раз для генерації сесії.

## Quick start (Docker)

```bash
cp .env.example .env  # edit with your values
docker compose up -d --build
# follow logs
docker compose logs -f
```

## Quick start (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m telegram_scraper.run
```

## Updating

Pull the latest changes and rebuild:

```bash
git pull
docker compose build
```

## Security

- Never commit your filled `.env` file.
- Keep your Telegram credentials safe.

## Telegram limits

Telegram enforces rate limits and may temporarily ban accounts that perform too many actions. Scrape responsibly.

## Troubleshooting

- Make sure the API credentials are valid.
- Check network access to Telegram and n8n.
- For proxy support and advanced options see TODOs in the code.
