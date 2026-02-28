import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен не найден! Добавьте BOT_TOKEN в .env файл.")

# Список администраторов (ID через запятую)
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
if not ADMIN_IDS:
    print("⚠️ ВНИМАНИЕ: Не указаны ADMIN_IDS. Админ-команды будут недоступны.")