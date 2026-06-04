import logging
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.i18n import t
from src.keyboards import (
    subscription_mode_keyboard,
    language_keyboard,
    team_subscribe_keyboard,
    team_unsubscribe_keyboard,
    main_menu_keyboard,
)
from src.match_repository import load_matches, get_all_teams
from src.user_repository import (
    create_user,
    get_user,
    set_language,
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


def _get_user_lang(chat_id: int) -> str:
    user = get_user(chat_id)
    return user["language"] if user else "es"


async def _reply(update: Update, text: str, **kwargs):
    if update.callback_query:
        try:
            await update.callback_query.message.reply_text(text, **kwargs)
        except BadRequest:
            pass
    elif update.message:
        await update.message.reply_text(text, **kwargs)


async def _edit(update: Update, text: str, **kwargs):
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, **kwargs)
        except BadRequest:
            await _reply(update, text, **kwargs)


def _format_match(m, user_tz: ZoneInfo, show_date: bool = False) -> str:
    try:
        kickoff = datetime.fromisoformat(m.kickoff_utc.replace("Z", "+00:00"))
        local = kickoff.astimezone(user_tz)
        if show_date:
            return f"📅 {local.strftime('%d/%m')}  🕒 {local.strftime('%H:%M')}  {m.home_team} vs {m.away_team}"
        return f"🕒 {local.strftime('%H:%M')}  {m.home_team} vs {m.away_team}"
    except (ValueError, TypeError):
        return f"{m.kickoff_utc}  {m.home_team} vs {m.away_team}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if user is None:
        create_user(chat_id, "UTC", "ALL")
        lang = "es"
        await _reply(update, t(lang, "welcome_new"), reply_markup=subscription_mode_keyboard(lang))
    else:
        lang = user["language"]
        await _reply(update, t(lang, "welcome_back"), reply_markup=main_menu_keyboard(lang))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = _get_user_lang(chat_id)
    await _reply(update, t(lang, "help"), parse_mode="Markdown")


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = _get_user_lang(chat_id)
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
        await _reply(update, t(lang, "no_matches_today"))
        return

    lines = [t(lang, "today_header")]
    for m in today_matches:
        lines.append("\n" + _format_match(m, user_tz))
    await _reply(update, "".join(lines), parse_mode="Markdown")


async def next_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = _get_user_lang(chat_id)
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
        await _reply(update, t(lang, "no_upcoming"))
        return

    lines = [t(lang, "upcoming_header")]
    for _, m in upcoming:
        lines.append("\n" + _format_match(m, user_tz, show_date=True))
    await _reply(update, "".join(lines), parse_mode="Markdown")


async def teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = _get_user_lang(chat_id)
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    text = t(lang, "teams_header") + "\n\n" + "\n".join(f"• {t}" for t in all_teams)
    await _reply(update, text, parse_mode="Markdown")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = _get_user_lang(chat_id)
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    selected = set(get_subscriptions(chat_id))
    context.user_data["sub_page"] = 0
    await _reply(update, t(lang, "subscribe_prompt"),
                 reply_markup=team_subscribe_keyboard(all_teams, selected, 0))


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = _get_user_lang(chat_id)
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    selected = set(get_subscriptions(chat_id))
    context.user_data["unsub_page"] = 0
    await _reply(update, t(lang, "unsubscribe_prompt"),
                 reply_markup=team_unsubscribe_keyboard(all_teams, selected, 0))


async def subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = _get_user_lang(chat_id)
    if user is None:
        await _reply(update, t(lang, "tz_not_started"))
        return

    mode_text = t(lang, "mode_all") if user["subscription_mode"] == "ALL" else t(lang, "mode_teams")
    lines = [t(lang, "mode_text", mode=mode_text)]

    if user["subscription_mode"] == "TEAMS":
        subs = get_subscriptions(chat_id)
        if subs:
            lines.append("\n" + t(lang, "subscriptions_header"))
            for s in subs:
                lines.append(f"\n  • {s}")
        else:
            lines.append("\n" + t(lang, "no_subscriptions"))
    else:
        lines.append(f"\n{t(lang, 'subscriptions_info')}")

    await _reply(update, "".join(lines), parse_mode="Markdown")


async def all_matches_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = _get_user_lang(chat_id)
    if user is None:
        await _reply(update, t(lang, "tz_not_started"))
        return
    set_subscription_mode(chat_id, "ALL")
    await _reply(update, t(lang, "mode_all_confirm"))


async def teams_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = _get_user_lang(chat_id)
    if user is None:
        await _reply(update, t(lang, "tz_not_started"))
        return
    set_subscription_mode(chat_id, "TEAMS")
    await _reply(update, t(lang, "mode_teams_confirm"))


async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = _get_user_lang(chat_id)
    if user is None:
        await _reply(update, t(lang, "tz_not_started"))
        return
    await _reply(update, t(lang, "language_prompt"), reply_markup=language_keyboard())


async def set_tz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = _get_user_lang(chat_id)
    if user is None:
        await _reply(update, t(lang, "tz_not_started"))
        return

    args = context.args
    if not args:
        await _reply(update, t(lang, "tz_usage"))
        return

    tz_str = " ".join(args)
    try:
        ZoneInfo(tz_str)
    except (KeyError, TypeError):
        await _reply(update, t(lang, "tz_invalid", tz_str))
        return

    set_timezone(chat_id, tz_str)
    await _reply(update, t(lang, "tz_success", tz_str))


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        logger.warning("Stale callback query ignored")
        return

    chat_id = update.effective_chat.id
    data = query.data
    matches = _get_matches()
    all_teams = get_all_teams(matches)
    lang = _get_user_lang(chat_id)

    # Language selection
    if data == "lang_en":
        set_language(chat_id, "en")
        lang = "en"
        await _edit(update, t(lang, "language_changed", t(lang, "lang_name")))
        return

    if data == "lang_es":
        set_language(chat_id, "es")
        await _edit(update, t("es", "language_changed", t("es", "lang_name")))
        return

    # Mode selection
    if data == "mode_ALL":
        set_subscription_mode(chat_id, "ALL")
        await _edit(update, t(lang, "mode_all_confirm"))
        return

    if data == "mode_TEAMS":
        set_subscription_mode(chat_id, "TEAMS")
        selected = set(get_subscriptions(chat_id))
        context.user_data["sub_page"] = 0
        await _edit(update, t(lang, "subscribe_prompt"),
                    reply_markup=team_subscribe_keyboard(all_teams, selected, 0))
        return

    # Subscribe flow
    if data.startswith("sub_"):
        selected = set(get_subscriptions(chat_id))
        page = context.user_data.get("sub_page", 0)

        if data == "sub_done":
            context.user_data.pop("sub_page", None)
            await _edit(update, t(lang, "subscriptions_updated"))
            return

        if data.startswith("sub_page:"):
            page = int(data.split(":")[1])
            context.user_data["sub_page"] = page
            await _edit(update, t(lang, "subscribe_prompt"),
                        reply_markup=team_subscribe_keyboard(all_teams, selected, page))
            return

        if data.startswith("sub_toggle:"):
            team = data.split(":", 1)[1]
            if team in selected:
                unsubscribe_team(chat_id, team)
                selected.discard(team)
            else:
                subscribe_team(chat_id, team)
                selected.add(team)
            await _edit(update, t(lang, "subscribe_prompt"),
                        reply_markup=team_subscribe_keyboard(all_teams, selected, page))
            return

    # Unsubscribe flow
    if data.startswith("unsub_"):
        selected = set(get_subscriptions(chat_id))
        page = context.user_data.get("unsub_page", 0)

        if data == "unsub_done":
            context.user_data.pop("unsub_page", None)
            await _edit(update, t(lang, "subscriptions_updated"))
            return

        if data.startswith("unsub_page:"):
            page = int(data.split(":")[1])
            context.user_data["unsub_page"] = page
            await _edit(update, t(lang, "unsubscribe_prompt"),
                        reply_markup=team_unsubscribe_keyboard(all_teams, selected, page))
            return

        if data.startswith("unsub_toggle:"):
            team = data.split(":", 1)[1]
            if team in selected:
                unsubscribe_team(chat_id, team)
                selected.discard(team)
            await _edit(update, t(lang, "unsubscribe_prompt"),
                        reply_markup=team_unsubscribe_keyboard(all_teams, selected, page))
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
    await _edit(update, t(lang, "unknown_option"))
