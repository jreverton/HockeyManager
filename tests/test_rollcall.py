import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import discord
import settings
from guild.models import AttendanceType
from tasks.rollCall import build_gametime_embed, get_role_mention_string, restore_startup_rollcalls, send_line_up


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
        result = asyncio.run(get_role_mention_string(cast(discord.Guild, guild), guild.text_channels[0], None))
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
        result = asyncio.run(get_role_mention_string(cast(discord.Guild, guild), guild.text_channels[0], cast(Any, channel_config)))
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
        message_id = asyncio.run(send_line_up(cast(discord.Guild, guild), "Alice", AttendanceType.SKATERS, channel, None))

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
        result = asyncio.run(send_line_up(cast(discord.Guild, guild), "Alice", AttendanceType.SKATERS, guild.text_channels[0], fake_message))

        # Existing roll call messages should be edited in-place, not created again.
        self.assertIsNone(result)
        fake_message.edit.assert_awaited_once()

    def test_build_gametime_embed_returns_expected_fields(self):
        game_datetime = datetime(2026, 6, 7, 19, 30, tzinfo=timezone.utc)
        embed = build_gametime_embed(game_datetime, "Sharks", "Ducks", "https://example.com/schedule")

        self.assertEqual(embed.title, "Next Game")
        self.assertEqual(embed.url, "https://example.com/schedule")
        self.assertEqual(len(embed.fields), 3)
        self.assertEqual(embed.fields[0].name, "Game Time:")
        self.assertEqual(embed.fields[0].value, "<t:1780860600:F>") # "Sunday June 07 at 07:30 PM" in unix timestamp
        self.assertEqual(embed.fields[1].name, "Home Team:")
        self.assertEqual(embed.fields[1].value, "Sharks")
        self.assertEqual(embed.fields[2].name, "Away Team:")
        self.assertEqual(embed.fields[2].value, "Ducks")

    @patch("tasks.rollCall.get_roll_call_channels")
    @patch("tasks.rollCall.get_channel_config")
    @patch("tasks.rollCall.schedule_parser.get_next_game")
    @patch("tasks.rollCall.get_role_mention_string", new_callable=AsyncMock)
    @patch("tasks.rollCall.lineup_embed")
    @patch("tasks.rollCall.schedule_reminder", new=Mock(return_value=None))
    @patch("tasks.rollCall.asyncio.create_task")
    def test_restore_startup_rollcalls_posts_embed_and_lineup(self, create_task, lineup_embed, get_role_mention_string, get_next_game, get_channel_config, get_roll_call_channels):
        channel = FakeChannel("roll-call")
        guild = FakeGuild(name="test-guild", text_channels=[channel])
        bot = Mock()
        bot.guilds = [guild]

        get_roll_call_channels.return_value = [channel]
        channel_config = {
            "next_game": datetime.now(timezone.utc) + timedelta(days=1),
            "attendance": {
                AttendanceType.SKATERS.value: [],
                AttendanceType.SUBS.value: [],
                AttendanceType.GOALIE.value: "",
                AttendanceType.OUT.value: [],
            },
        }
        get_channel_config.return_value = channel_config

        fake_game = Mock()
        fake_game.datetime = channel_config["next_game"]
        fake_game.home_team = "Sharks"
        fake_game.away_team = "Ducks"
        get_next_game.return_value = ("https://example.com/schedule", fake_game)

        get_role_mention_string.return_value = "@everyone"
        lineup_embed.return_value = discord.Embed(title="Current Line Up")

        asyncio.run(restore_startup_rollcalls(bot))

        self.assertGreaterEqual(channel.send.await_count, 3)
        self.assertEqual(channel.sent[0][1]["embed"].title, "Next Game")
        self.assertEqual(channel.sent[1][1]["embed"].title, "Current Line Up")
        self.assertIn("view", channel.sent[2][1])

