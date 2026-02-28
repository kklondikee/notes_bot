import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import database as db

scheduler = AsyncIOScheduler()

async def check_reminders(bot: Bot):
    """Проверяет просроченные напоминания и отправляет их."""
    reminders = db.get_pending_reminders()
    for note_id, user_id, title, text in reminders:
        await bot.send_message(
            user_id,
            f"⏰ *Напоминание:* {title}\n\n{text}",
            parse_mode="Markdown"
        )
        db.mark_reminder_sent(note_id)

def start_scheduler(bot: Bot):
    """Запускает планировщик с задачей проверки раз в минуту."""
    scheduler.add_job(
        check_reminders,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],
        id="reminder_check",
        replace_existing=True
    )
    scheduler.start()