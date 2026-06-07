import os
import sys
import unittest
import asyncio
import discord
from typing import cast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SEASON_ID = 14815
gs_division_id = 79353
gs_team_id = 513679
PLAYER_ID = 7998339
PLAYER_NAME = 'James Everton'

from cmds.team import fetch_team_data, fetch_division_standings
from cmds.player import pull_player_stats


class TestGameSheetAPI(unittest.TestCase):
    # Verify the team summary API returns the expected team-level fields
    def test_fetch_team_data_returns_expected_fields(self):
        team_data = fetch_team_data(SEASON_ID, gs_team_id)
        assert team_data is not None
        self.assertIsInstance(team_data, dict)
        self.assertIn('title', team_data)
        self.assertIn('record', team_data)
        self.assertIn('pts', team_data)
        self.assertIn('rank', team_data)
        self.assertIn('division', team_data)
        self.assertIsInstance(team_data['division'], dict)
        self.assertIn('id', team_data['division'])
        self.assertIn('title', team_data['division'])

    # Verify the division standings API returns a valid structure with expected columns
    def test_fetch_division_standings_returns_expected_structure(self):
        standings = fetch_division_standings(SEASON_ID, gs_division_id)
        assert standings is not None
        self.assertIsInstance(standings, list)
        self.assertGreater(len(standings), 0)

        first_group = standings[0]
        self.assertIn('tableData', first_group)
        table_data = first_group['tableData']
        self.assertIsInstance(table_data, dict)
        self.assertIn('teamIds', table_data)
        self.assertIn('teamTitles', table_data)
        self.assertIn('pts', table_data)
        self.assertIn('gp', table_data)
        self.assertIn('w', table_data)
        self.assertIn('l', table_data)
        self.assertIn('otw', table_data)
        self.assertIn('sow', table_data)
        self.assertIn('otl', table_data)
        self.assertIn('sol', table_data)
        self.assertIn('pim', table_data)
        self.assertTrue(all(isinstance(team, dict) for team in table_data['teamTitles']))
        self.assertTrue(all('title' in team and 'id' in team for team in table_data['teamTitles']))

    # Verify the command wrapper can resolve guild/channel config and return standings rows
    def test_get_team_standings_returns_rows(self):
        import cmds.team as team_module

        class DummyChannel:
            name = 'test'
            async def send(self, message):
                pass

        def fake_get_guild_config(guild):
            return {'season_id': SEASON_ID}

        def fake_get_channel_config(guild, name):
            return {'gs_team_id': gs_team_id}

        team_module.get_guild_config = fake_get_guild_config
        team_module.get_channel_config = fake_get_channel_config

        rows = asyncio.run(team_module.get_team_standings(cast(discord.Guild, object()), cast(discord.TextChannel, DummyChannel())))
        assert rows is not None
        self.assertIsInstance(rows, list)
        self.assertGreater(len(rows), 0)
        self.assertEqual(len(rows[0]), 12)

    # Verify the player stats wrapper returns an embed for a matching player name
    def test_pull_player_stats_returns_embed(self):
        import cmds.player as player_module

        class DummyChannel:
            name = 'test'
            async def send(self, message):
                pass

        def fake_get_guild_config(guild):
            return {'season_id': SEASON_ID}

        def fake_get_channel_config(guild, name):
            return {'gs_team_id': gs_team_id}

        player_module.get_guild_config = fake_get_guild_config
        player_module.get_channel_config = fake_get_channel_config

        embed = asyncio.run(player_module.pull_player_stats(cast(discord.Guild, object()), cast(discord.TextChannel, DummyChannel()), PLAYER_NAME))
        assert embed is not None
        self.assertIsNotNone(embed)
        self.assertIsInstance(embed, discord.Embed)
        self.assertIsNotNone(embed.title)
        self.assertIn('JAMES EVERTON', cast(str, embed.title))


if __name__ == '__main__':
    unittest.main()
