import json
import logging
from pathlib import Path
from typing import Optional

from src.models import Match

logger = logging.getLogger(__name__)


def load_matches(path: str | Path) -> list[Match]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        Match(
            id=item["id"],
            home_team=item["home_team"],
            away_team=item["away_team"],
            phase=item["phase"],
            stadium=item.get("stadium", ""),
            city=item.get("city", ""),
            kickoff_utc=item["kickoff_utc"],
        )
        for item in data
    ]


def get_match_by_id(matches: list[Match], match_id: str) -> Optional[Match]:
    for m in matches:
        if m.id == match_id:
            return m
    return None


def get_matches_for_team(matches: list[Match], team: str) -> list[Match]:
    return [m for m in matches if m.home_team == team or m.away_team == team]


def get_all_teams(matches: list[Match]) -> list[str]:
    teams: set[str] = set()
    for m in matches:
        teams.add(m.home_team)
        teams.add(m.away_team)
    return sorted(teams)
