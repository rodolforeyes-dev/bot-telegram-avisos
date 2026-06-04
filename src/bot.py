import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from src.config import TELEGRAM_BOT_TOKEN, ICS_PATH, MATCHES_PATH
from src.database import init_db
from src.fixture_importer import needs_import, run_import
from src.command_handlers import (
    start,
    help_command,
    today,
    next_matches,
    teams,
    subscribe,
    unsubscribe,
    subscriptions,
    all_matches_mode,
    teams_mode,
    set_tz,
    language_cmd,
    callback_handler,
)
from src.scheduler import check_match_reminders, check_daily_summaries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled error: %s", context.error, exc_info=context.error)


async def post_init(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_match_reminders, "interval", minutes=5, args=[app.bot])
    scheduler.add_job(check_daily_summaries, "interval", hours=1, args=[app.bot])
    scheduler.start()
    logger.info("Schedulers started")


def main():
    logging.info("Starting FIFA World Cup 2026 Bot")

    init_db()

    if needs_import(MATCHES_PATH):
        if ICS_PATH.exists():
            run_import(ICS_PATH, MATCHES_PATH)
        else:
            logger.warning("ICS file not found at %s", ICS_PATH)
    else:
        logger.info("Matches already imported")

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Create a .env file with TELEGRAM_BOT_TOKEN=your_token")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("next", next_matches))
    app.add_handler(CommandHandler("teams", teams))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("subscriptions", subscriptions))
    app.add_handler(CommandHandler("all", all_matches_mode))
    app.add_handler(CommandHandler("teamsmode", teams_mode))
    app.add_handler(CommandHandler("timezone", set_tz))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_error_handler(error_handler)

    logger.info("Bot started polling")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
