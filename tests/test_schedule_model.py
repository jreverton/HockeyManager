import unittest
from datetime import datetime, timezone

from schedule.model import Schedule


class TestScheduleModel(unittest.TestCase):
    def test_from_dict_accepts_iso_datetime_string(self):
        data = {
            "home_team": "Home",
            "away_team": "Away",
            "datetime": "2026-06-01T18:00:00+00:00",
            "rink": "Arena",
        }

        # The Schedule model should parse an ISO 8601 datetime string into a timezone-aware object.
        schedule = Schedule.from_dict(data)

        self.assertEqual(schedule.home_team, "Home")
        self.assertEqual(schedule.away_team, "Away")
        self.assertEqual(schedule.rink, "Arena")
        self.assertEqual(schedule.datetime, datetime(2026, 6, 1, 18, 0, tzinfo=timezone.utc))

    def test_from_dict_rejects_invalid_datetime(self):
        data = {
            "home_team": "Home",
            "away_team": "Away",
            "datetime": None,
            "rink": "Arena",
        }

        # Invalid datetime input should raise a ValueError rather than silently accepting bad data.
        with self.assertRaises(ValueError):
            Schedule.from_dict(data)
