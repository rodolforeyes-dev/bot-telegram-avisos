from dataclasses import dataclass


@dataclass
class Match:
    id: str
    home_team: str
    away_team: str
    phase: str
    stadium: str
    city: str
    kickoff_utc: str


@dataclass
class User:
    chat_id: int
    timezone: str
    subscription_mode: str
    notify_before_minutes: int = 120


@dataclass
class Subscription:
    chat_id: int
    team_name: str


@dataclass
class SentNotification:
    chat_id: int
    match_id: str
    notification_type: str
