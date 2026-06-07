import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

import settings
from guild.models import AttendanceType
from tasks.rollCall import get_role_mention_string, send_line_up


class FakeRole:
    def __init__(self, name: str, mention: str):
        self.name = name
        self.mention = mention


class FakeMember:
    def __init__(self, name: str, mention: str):
        self.name = name
        self.mention = mention


class FakeChannel:
    def __init__(self, name: str):
        self.name = name
        self.send = AsyncMock(side_effect=self._send)
        self.sent = []

    async def _send(self, *args, **kwargs):
        message = Mock()
        message.id = 123
        message.edit = AsyncMock()
        self.sent.append((args, kwargs))
        return message


class FakeGuild:
    def __init__(self, name: str, roles=None, text_channels=None, members=None):
        self.name = name
        self.roles = roles or []
        self.text_channels = text_channels or []
        self._members = members or []

    def get_member_named(self, user_name: str):
        for member in self._members:
            if member.name == user_name:
                return member
        return None


class TestRollCallHelpers(unittest.TestCase):
    def setUp(self):
        self.saved_config = settings.SERVER_CONFIG.copy()

    def tearDown(self):
        settings.SERVER_CONFIG.clear()
        settings.SERVER_CONFIG.update(self.saved_config)

    def test_get_role_mention_string_returns_everyone_when_no_role_names(self):
        guild = FakeGuild(
            name="test-guild",
            roles=[],
            text_channels=[FakeChannel("test-channel")],
        )

        # When no role names are configured, roll call should default to the everyone mention.
        result = asyncio.run(get_role_mention_string(guild, guild.text_channels[0], None))
        self.assertEqual(result, "@everyone")

    def test_get_role_mention_string_mentions_existing_role(self):
        role = FakeRole(name="Tata", mention="@Tata")
        guild = FakeGuild(
            name="test-guild",
            roles=[role],
            text_channels=[FakeChannel("test-channel")],
        )
        channel_config = {
            "role_names": ["Tata"],
        }

        # Verify that an existing configured role is converted into the role mention string.
        result = asyncio.run(get_role_mention_string(guild, guild.text_channels[0], channel_config))
        self.assertEqual(result, " @Tata")

    def test_send_line_up_creates_message_and_updates_attendance(self):
        guild = FakeGuild(
            name="test-guild",
            roles=[],
            text_channels=[FakeChannel("roll-call")],
            members=[FakeMember("Alice", "@Alice")],
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
                    "team_calendar_id": "uuid",
                    "gs_team_id": 0,
                    "role_names": [],
                    "next_game": None,
                    "attendance": {
                        AttendanceType.SKATERS.value: [],
                        AttendanceType.SUBS.value: [],
                        AttendanceType.GOALIE.value: "",
                        AttendanceType.OUT.value: [],
                    },
                }
            ],
        }

        channel = guild.text_channels[0]
        message_id = asyncio.run(send_line_up(guild, "Alice", AttendanceType.SKATERS, channel, None))

        # A new roll call message should be sent and the returned ID should match the created message.
        self.assertEqual(message_id, 123)
        saved_attendance = settings.SERVER_CONFIG["test-guild"]["channels"][0]["attendance"]
        self.assertEqual(saved_attendance[AttendanceType.SKATERS.value], ["@Alice"])

    def test_send_line_up_edits_existing_message(self):
        guild = FakeGuild(
            name="test-guild",
            roles=[],
            text_channels=[FakeChannel("roll-call")],
            members=[FakeMember("Alice", "@Alice")],
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
                    "team_calendar_id": "uuid",
                    "gs_team_id": 0,
                    "role_names": [],
                    "next_game": None,
                    "attendance": {
                        AttendanceType.SKATERS.value: [],
                        AttendanceType.SUBS.value: [],
                        AttendanceType.GOALIE.value: "",
                        AttendanceType.OUT.value: [],
                    },
                }
            ],
        }

        fake_message = Mock()
        fake_message.edit = AsyncMock()
        result = asyncio.run(send_line_up(guild, "Alice", AttendanceType.SKATERS, guild.text_channels[0], fake_message))

        # Existing roll call messages should be edited in-place, not created again.
        self.assertIsNone(result)
        fake_message.edit.assert_awaited_once()

