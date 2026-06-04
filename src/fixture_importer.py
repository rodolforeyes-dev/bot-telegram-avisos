import json
import logging
from pathlib import Path
from typing import Optional

from icalendar import Calendar

from src.models import Match

logger = logging.getLogger(__name__)


def parse_vevent(summary: str) -> tuple[str, str, str]:
    parts = summary.split(" - FIFA World Cup 2026 ", 1)
    if len(parts) != 2:
        return "", "", summary
    teams_part, phase = parts
    phase = phase.strip()
    if " vs " not in teams_part:
        return "", "", phase
    home, away = teams_part.split(" vs ", 1)
    return home.strip(), away.strip(), phase.strip()


def infer_city(stadium: str) -> str:
    city = stadium
    for suffix in (" Stadium", " Arena", " BC Place"):
        if city.endswith(suffix):
            city = city[: -len(suffix)]
            break
    return city


def extract_matches(ics_path: str | Path) -> list[Match]:
    with open(ics_path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    matches = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("summary", ""))
        home_team, away_team, phase = parse_vevent(summary)
        if not home_team or not away_team:
            logger.warning("Skipping unparseable event: %s", summary)
            continue

        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        kickoff_utc = dtstart.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        uid = str(component.get("uid", ""))
        match_id = uid.split("@")[0] if "@" in uid else f"match-{len(matches)}"

        stadium = str(component.get("location", ""))

        matches.append(Match(
            id=f"match-{match_id}",
            home_team=home_team,
            away_team=away_team,
            phase=phase,
            stadium=stadium,
            city=infer_city(stadium),
            kickoff_utc=kickoff_utc,
        ))

    return matches


def save_matches(matches: list[Match], output_path: str | Path):
    data = [
        {
            "id": m.id,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "phase": m.phase,
            "stadium": m.stadium,
            "city": m.city,
            "kickoff_utc": m.kickoff_utc,
        }
        for m in matches
    ]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d matches to %s", len(matches), output_path)


def needs_import(output_path: str | Path) -> bool:
    return not Path(output_path).exists()


def run_import(ics_path: str | Path, output_path: str | Path) -> list[Match]:
    logger.info("Importing fixtures from %s", ics_path)
    matches = extract_matches(ics_path)
    save_matches(matches, output_path)
    return matches
