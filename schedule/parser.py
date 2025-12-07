import discord
from guild.config import get_guild_config
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urlencode
from schedule import Schedule
from typing import List
from guild import ChannelConfig, get_channel_config


TEAM_NAME_CLASS = 'nova-title'

SCHEDULE_TABLE_CLASS = 'table'

SCHEDULE_DATETIME_FORMAT = '%a, %b %d %I:%M %p'

BASE_SCHEDULE_URL = 'https://stats.pointstreak.com/players/players-team-schedule.html'


def retrieve_team_data(team_id, season_id) -> tuple[str, str, List[Schedule]]:
    schedule_url = '{}?{}'.format(BASE_SCHEDULE_URL, urlencode({'seasonid': season_id, 'teamid': team_id}))
    schedule_html = retrieve_schedule(schedule_url)

    team_name, schedule_data = parse_schedule(schedule_html)
    return team_name, schedule_url, schedule_data


def retrieve_schedule(schedule_url):
    print('GET {}'.format(schedule_url))
    r = requests.get(schedule_url)
    return r.text


def parse_schedule(schedule_html) -> tuple[str, List[Schedule]]:
    schedule_data: List[Schedule] = []
    current_year = datetime.now().year

    soup = BeautifulSoup(schedule_html, 'html.parser')

    team_name_group = soup.find_all('span', class_=TEAM_NAME_CLASS)[0]
    team_name_span = team_name_group.find_all('span')[0]
    team_name = team_name_span.text

    schedule_table = soup.find_all('table', class_=SCHEDULE_TABLE_CLASS)[0]
    schedule_body = schedule_table.find_all('tbody')[0]
    schedule_rows = schedule_body.find_all('tr')

    for row in schedule_rows:
        columns = row.find_all('td')

        column_values = [c.text.strip() for c in columns]

        home, away, date_str, time_str, rink = column_values

        datetime_str = '{} {}'.format(date_str, time_str)

        parsed_datetime = datetime.strptime(datetime_str, SCHEDULE_DATETIME_FORMAT)

        # TODO: Handle schedules with current year and next year
        game_datetime = parsed_datetime.replace(year=current_year)

        # make datetime timezone-aware (UTC) so it matches Schedule expectations
        game_datetime = game_datetime.replace(tzinfo=timezone.utc)

        schedule_data.append(Schedule(
            home_team=home,
            away_team=away,
            datetime=game_datetime,
            rink=rink,
        ))

    return team_name, schedule_data


def filter_upcoming_games(schedule_data: List[Schedule]) -> List[Schedule]:
    now = datetime.now(timezone.utc)
    upcoming_games = [game for game in schedule_data if game.datetime > now]
    return upcoming_games


def get_next_game_from_schedules(schedule_data: List[Schedule]) -> Schedule|None:
    upcoming_games = filter_upcoming_games(schedule_data)
    if not upcoming_games:
        return None
    next_game = min(upcoming_games, key=lambda game: game.datetime)
    return next_game


# TODO JRE: Move this over to rollCall.py, but using the bot context instead of the user command context
"""
Returns the schedule URL and next game for the guild's configured team and season.
"""
def get_next_game(guild: discord.Guild, channel_name: str) -> tuple[str, Schedule|None]: # schedule_url, next_game
    # Find the first channel config whose 'name' property equals channel_name
    guild_data = get_guild_config(guild)
    channel_data: ChannelConfig | None = get_channel_config(guild, channel_name)
    if channel_data is None:
        return "", None

    _, schedule_url, schedule_data = retrieve_team_data(channel_data["team_id"], guild_data["season_id"])
    next_game = get_next_game_from_schedules(schedule_data)

    return schedule_url, next_game
