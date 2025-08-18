import os
from telethon.sync import TelegramClient
from pathlib import Path

api_id = int(os.environ.get("TG_API_ID"))
api_hash = os.environ.get("TG_API_HASH")

session_path = Path("./sessions/zhito_admin")
client = TelegramClient(session_path, api_id, api_hash)

with client:
    print("✅ Сесія збережена у", session_path)
