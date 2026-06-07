"""Type definitions for guild configuration and related structures."""

from datetime import datetime
from enum import StrEnum
from typing import TypedDict


class AttendanceType(StrEnum):
    """Enum of attendance categories"""
    SKATERS = "Skaters"
    SUBS = "Subs"
    GOALIE = "Goalie"
    OUT = "Out"


class AttendanceDict(TypedDict):
    """Structure for tracking player attendance by category."""
    Skaters: list[str]
    Subs: list[str]
    Goalie: str
    Out: list[str]


class ChannelConfig(TypedDict):
    """Structure for per-channel configuration (roll-call channels)."""
    name: str
    channel_id: int
    team_calendar_id: str
    gs_team_id: int
    role_names: list[str]
    next_game: datetime | None
    attendance: AttendanceDict


class GuildConfig(TypedDict):
    """Structure for guild-level configuration."""
    id: int
    bot_channel: int
    file_prefix: str
    roll_call_channel_suffix: str
    season_id: int
    channels: list[ChannelConfig]


# Type alias for the entire SERVER_CONFIG structure
# Example: { "guild_name": GuildConfig, ... }
ServerConfigDict = dict[str, GuildConfig]

