import os
import sys
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import helper
import settings
from schedule.model import Schedule


class TestHelperPullSchedule(unittest.TestCase):
    def setUp(self):
        self.saved_config = settings.SERVER_CONFIG.copy()

    def tearDown(self):
        settings.SERVER_CONFIG.clear()
        settings.SERVER_CONFIG.update(self.saved_config)

    def test_pull_schedule_returns_game_fields_from_gamesheets(self):
        schedule_item = Schedule(
            home_team="Home Team",
            away_team="Away Team",
            datetime=datetime(2026, 6, 1, 18, 0, tzinfo=timezone.utc),
            rink="Arena"
        )

        settings.SERVER_CONFIG["test-guild"] = {
            "id": 1,
            "bot_channel": 0,
            "file_prefix": "test",
            "roll_call_channel_suffix": "-roll-call",
            "season_id": 0,
            "channels": [
                {
                    "name": "roll-call",
                    "channel_id": 123,
                    "team_calendar_id": "abc123",
                    "gs_team_id": 0,
                    "role_names": [],
                    "next_game": None,
                    "attendance": {
                        "Skaters": [],
                        "Subs": [],
                        "Goalie": "",
                        "Out": []
                    },
                }
            ],
        }

        with patch("helper.retrieve_team_data", return_value=("Team Name", "https://example.com/calendar.ics", [schedule_item])):
            home_teams, away_teams, game_days, game_times = helper.pull_schedule("test-guild")

        self.assertEqual(home_teams, ["Home Team"])
        self.assertEqual(away_teams, ["Away Team"])
        self.assertEqual(game_days, ["Mon, Jun 01"])
        self.assertEqual(game_times, ["6:00 PM"])

    def test_pull_schedule_returns_empty_when_no_team_calendar_id(self):
        settings.SERVER_CONFIG["test-guild"] = {
            "id": 1,
            "bot_channel": 0,
            "file_prefix": "test",
            "roll_call_channel_suffix": "-roll-call",
            "season_id": 0,
            "channels": [
                {
                    "name": "roll-call",
                    "channel_id": 123,
                    "team_calendar_id": "0",
                    "gs_team_id": 0,
                    "role_names": [],
                    "next_game": None,
                    "attendance": {
                        "Skaters": [],
                        "Subs": [],
                        "Goalie": "",
                        "Out": []
                    },
                }
            ],
        }

        home_teams, away_teams, game_days, game_times = helper.pull_schedule("test-guild")

        self.assertEqual(home_teams, [])
        self.assertEqual(away_teams, [])
        self.assertEqual(game_days, [])
        self.assertEqual(game_times, [])


if __name__ == "__main__":
    unittest.main()
