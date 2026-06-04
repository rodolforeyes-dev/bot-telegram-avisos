import logging
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from src.keyboards import (
    subscription_mode_keyboard,
    team_subscribe_keyboard,
    team_unsubscribe_keyboard,
    main_menu_keyboard,
)
from src.match_repository import load_matches, get_all_teams
from src.user_repository import (
    create_user,
    get_user,
    set_timezone,
    set_subscription_mode,
    subscribe_team,
    unsubscribe_team,
    get_subscriptions,
)
from src.config import MATCHES_PATH

logger = logging.getLogger(__name__)

_matches_cache: list | None = None


def _get_matches():
    global _matches_cache
    if _matches_cache is None:
        try:
            _matches_cache = load_matches(MATCHES_PATH)
        except Exception:
            logger.exception("Failed to load matches")
            _matches_cache = []
    return _matches_cache


def _get_user_tz(chat_id: int) -> ZoneInfo:
    user = get_user(chat_id)
    if user is None:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(user["timezone"])
    except (KeyError, TypeError):
        return ZoneInfo("UTC")


def _format_match(m, user_tz: ZoneInfo) -> str:
    try:
        kickoff = datetime.fromisoformat(m.kickoff_utc.replace("Z", "+00:00"))
        local = kickoff.astimezone(user_tz)
        time_str = local.strftime("%H:%M")
    except (ValueError, TypeError):
        time_str = m.kickoff_utc
    return f"🕒 {time_str}  {m.home_team} vs {m.away_team}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if user is None:
        create_user(chat_id, "UTC", "ALL")
        await update.message.reply_text(
            "👋 Welcome to FIFA World Cup 2026 Bot!\n\n"
            "How would you like to receive notifications?",
            reply_markup=subscription_mode_keyboard(),
        )
    else:
        await update.message.reply_text(
            "Welcome back! Use /help to see available commands.",
            reply_markup=main_menu_keyboard(),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Available Commands*\n\n"
        "/start - Restart the bot\n"
        "/help - Show this message\n"
        "/today - Today's matches\n"
        "/next - Upcoming matches\n"
        "/teams - List all teams\n"
        "/subscribe - Subscribe to teams\n"
        "/unsubscribe - Remove subscriptions\n"
        "/subscriptions - Your subscriptions\n"
        "/all - Notify for ALL matches\n"
        "/teamsmode - Notify for selected teams only\n"
        "/timezone - Set your timezone"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_tz = _get_user_tz(chat_id)
    now = datetime.now(user_tz)
    matches = _get_matches()

    today_matches = []
    for m in matches:
        try:
            kickoff = datetime.fromisoformat(m.kickoff_utc.replace("Z", "+00:00"))
            local = kickoff.astimezone(user_tz)
            if local.date() == now.date():
                today_matches.append(m)
        except (ValueError, TypeError):
            continue

    if not today_matches:
        await update.message.reply_text("No matches scheduled for today.")
        return

    lines = ["⚽ *Today's matches*\n"]
    for m in today_matches:
        lines.append(_format_match(m, user_tz))
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def next_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    user_tz = _get_user_tz(chat_id)
    now = datetime.now(dt_timezone.utc)
    matches = _get_matches()

    if user and user["subscription_mode"] == "TEAMS":
        subs = get_subscriptions(chat_id)
        relevant = [m for m in matches if m.home_team in subs or m.away_team in subs]
    else:
        relevant = list(matches)

    upcoming = []
    for m in relevant:
        try:
            kickoff = datetime.fromisoformat(m.kickoff_utc.replace("Z", "+00:00"))
            if kickoff > now:
                upcoming.append((kickoff, m))
        except (ValueError, TypeError):
            continue

    upcoming.sort(key=lambda x: x[0])
    upcoming = upcoming[:10]

    if not upcoming:
        await update.message.reply_text("No upcoming matches.")
        return

    lines = ["⚽ *Upcoming matches*\n"]
    for _, m in upcoming:
        lines.append(_format_match(m, user_tz))
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    text = "🏆 *Available teams*\n\n" + "\n".join(f"• {t}" for t in all_teams)
    await update.message.reply_text(text, parse_mode="Markdown")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    selected = set(get_subscriptions(chat_id))
    context.user_data["sub_page"] = 0
    await update.message.reply_text(
        "Select teams to subscribe:",
        reply_markup=team_subscribe_keyboard(all_teams, selected, 0),
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    selected = set(get_subscriptions(chat_id))
    context.user_data["unsub_page"] = 0
    await update.message.reply_text(
        "Select teams to unsubscribe:",
        reply_markup=team_unsubscribe_keyboard(all_teams, selected, 0),
    )


async def subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if user is None:
        await update.message.reply_text("Please use /start first.")
        return

    mode_text = "🌎 All matches" if user["subscription_mode"] == "ALL" else "⭐ Selected teams"
    lines = [f"*Mode:* {mode_text}\n"]

    if user["subscription_mode"] == "TEAMS":
        subs = get_subscriptions(chat_id)
        if subs:
            lines.append("*Your subscriptions:*")
            for s in subs:
                lines.append(f"  • {s}")
        else:
            lines.append("No subscriptions yet. Use /subscribe to add teams.")
    else:
        lines.append("You are subscribed to all matches.")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def all_matches_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if user is None:
        await update.message.reply_text("Please use /start first.")
        return
    set_subscription_mode(chat_id, "ALL")
    await update.message.reply_text("✅ You will now receive notifications for every World Cup match.")


async def teams_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if user is None:
        await update.message.reply_text("Please use /start first.")
        return
    set_subscription_mode(chat_id, "TEAMS")
    await update.message.reply_text(
        "✅ Team subscription mode enabled.\n"
        "Use /subscribe to choose your teams."
    )


async def set_tz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if user is None:
        await update.message.reply_text("Please use /start first.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /timezone <timezone>\n\n"
            "Examples:\n"
            "• America/Argentina/Buenos_Aires\n"
            "• Europe/Madrid\n"
            "• America/Mexico_City\n"
            "• America/New_York"
        )
        return

    tz_str = " ".join(args)
    try:
        ZoneInfo(tz_str)
    except (KeyError, TypeError):
        await update.message.reply_text(f"❌ Invalid timezone: {tz_str}")
        return

    set_timezone(chat_id, tz_str)
    await update.message.reply_text(f"✅ Timezone set to {tz_str}")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    data = query.data
    matches = _get_matches()
    all_teams = get_all_teams(matches)

    # Mode selection
    if data == "mode_ALL":
        set_subscription_mode(chat_id, "ALL")
        await query.edit_message_text(
            "✅ You will now receive notifications for every World Cup match.\n\n"
            "Use /help to see all commands."
        )
        return

    if data == "mode_TEAMS":
        set_subscription_mode(chat_id, "TEAMS")
        selected = set(get_subscriptions(chat_id))
        context.user_data["sub_page"] = 0
        await query.edit_message_text(
            "Select your teams:",
            reply_markup=team_subscribe_keyboard(all_teams, selected, 0),
        )
        return

    # Subscribe flow
    if data.startswith("sub_"):
        selected = set(get_subscriptions(chat_id))
        page = context.user_data.get("sub_page", 0)

        if data == "sub_done":
            context.user_data.pop("sub_page", None)
            await query.edit_message_text("✅ Subscriptions updated!")
            return

        if data.startswith("sub_page:"):
            page = int(data.split(":")[1])
            context.user_data["sub_page"] = page
            await query.edit_message_text(
                "Select teams to subscribe:",
                reply_markup=team_subscribe_keyboard(all_teams, selected, page),
            )
            return

        if data.startswith("sub_toggle:"):
            team = data.split(":", 1)[1]
            if team in selected:
                unsubscribe_team(chat_id, team)
                selected.discard(team)
            else:
                subscribe_team(chat_id, team)
                selected.add(team)
            await query.edit_message_text(
                "Select teams to subscribe:",
                reply_markup=team_subscribe_keyboard(all_teams, selected, page),
            )
            return

    # Unsubscribe flow
    if data.startswith("unsub_"):
        selected = set(get_subscriptions(chat_id))
        page = context.user_data.get("unsub_page", 0)

        if data == "unsub_done":
            context.user_data.pop("unsub_page", None)
            await query.edit_message_text("✅ Subscriptions updated!")
            return

        if data.startswith("unsub_page:"):
            page = int(data.split(":")[1])
            context.user_data["unsub_page"] = page
            await query.edit_message_text(
                "Select teams to unsubscribe:",
                reply_markup=team_unsubscribe_keyboard(all_teams, selected, page),
            )
            return

        if data.startswith("unsub_toggle:"):
            team = data.split(":", 1)[1]
            if team in selected:
                unsubscribe_team(chat_id, team)
                selected.discard(team)
            await query.edit_message_text(
                "Select teams to unsubscribe:",
                reply_markup=team_unsubscribe_keyboard(all_teams, selected, page),
            )
            return

    # Main menu shortcuts
    if data == "cmd_today":
        await today(update, context)
        return
    if data == "cmd_next":
        await next_matches(update, context)
        return
    if data == "cmd_subscriptions":
        await subscriptions(update, context)
        return

    logger.warning("Unknown callback data: %s", data)
    await query.edit_message_text("Unknown option. Please use /help.")
