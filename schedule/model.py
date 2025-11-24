# schedule/model.py

from dataclasses import dataclass, asdict
from datetime import datetime as _dt
from typing import Any, Dict
import json


@dataclass(frozen=True)
class Schedule:
    """
    Schedule model representing a single game.
    Fields:
      - home_team: name of the home team
      - away_team: name of the away team
      - datetime: timezone-aware datetime of the game (datetime.datetime)
      - rink: rink name
    """
    home_team: str
    away_team: str
    datetime: _dt
    rink: str

    def __post_init__(self) -> None:
        if not isinstance(self.home_team, str) or not self.home_team:
            raise ValueError("home_team must be a non-empty string")
        if not isinstance(self.away_team, str) or not self.away_team:
            raise ValueError("away_team must be a non-empty string")
        if self.home_team == self.away_team:
            raise ValueError("home_team and away_team must be different")
        if not isinstance(self.datetime, _dt):
            raise TypeError("datetime must be a datetime.datetime instance")
        # require timezone-aware datetimes for safe sharing
        if self.datetime.tzinfo is None or self.datetime.tzinfo.utcoffset(self.datetime) is None:
            raise ValueError("datetime must be timezone-aware")
        if not isinstance(self.rink, str) or not self.rink:
            raise ValueError("rink must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict (datetime as ISO string)."""
        data = asdict(self)
        data["datetime"] = self.datetime.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Deserialize from dict produced by to_dict. Accepts ISO datetime string or datetime."""
        dt = data.get("datetime")
        if isinstance(dt, str):
            # datetime.fromisoformat supports offsets; if input may contain 'Z', convert it first
            if dt.endswith("Z"):
                dt = dt[:-1] + "+00:00"
            dt = _dt.fromisoformat(dt)
        return cls(
            home_team=data["home_team"],
            away_team=data["away_team"],
            datetime=dt,
            rink=data["rink"],
        )

    def to_json(self) -> str:
        """JSON string representation."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, s: str) -> "Schedule":
        return cls.from_dict(json.loads(s))