from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.i18n import t

PAGE_SIZE = 10


def subscription_mode_keyboard(lang: str = "es") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "mode_btn_all"), callback_data="mode_ALL")],
        [InlineKeyboardButton(t(lang, "mode_btn_teams"), callback_data="mode_TEAMS")],
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇦🇷 Español", callback_data="lang_es")],
    ])


def team_subscribe_keyboard(teams: list[str], selected: set[str], page: int) -> InlineKeyboardMarkup:
    return _team_pagination(teams, selected, page, "sub")


def team_unsubscribe_keyboard(teams: list[str], selected: set[str], page: int) -> InlineKeyboardMarkup:
    return _team_pagination(teams, selected, page, "unsub")


def _team_pagination(all_teams: list[str], selected: set[str], page: int, prefix: str) -> InlineKeyboardMarkup:
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_teams = all_teams[start:end]
    total_pages = (len(all_teams) + PAGE_SIZE - 1) // PAGE_SIZE

    keyboard = []
    for team in page_teams:
        checked = "✅" if team in selected else "⬜"
        keyboard.append([
            InlineKeyboardButton(f"{checked} {team}", callback_data=f"{prefix}_toggle:{team}")
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"{prefix}_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"{prefix}_page:{page + 1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("✅ Done", callback_data=f"{prefix}_done")])
    return InlineKeyboardMarkup(keyboard)


def main_menu_keyboard(lang: str = "es") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "main_today"), callback_data="cmd_today")],
        [InlineKeyboardButton(t(lang, "main_next"), callback_data="cmd_next")],
        [InlineKeyboardButton(t(lang, "main_subs"), callback_data="cmd_subscriptions")],
    ])
