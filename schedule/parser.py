import argparse
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pprint import pprint
from urllib.parse import urlencode
from schedule.model import Schedule
from typing import List


TEAM_NAME_CLASS = 'nova-title'

SCHEDULE_TABLE_CLASS = 'table'

SCHEDULE_DATETIME_FORMAT = '%a, %b %d %I:%M %p'

BASE_SCHEDULE_URL = 'https://stats.pointstreak.com/players/players-team-schedule.html'


def get_team_data(team_id, season_id) -> tuple[str, List[Schedule]]:
    schedule_url = '{}?{}'.format(BASE_SCHEDULE_URL, urlencode({'seasonid': season_id, 'teamid': team_id}))
    schedule_html = get_schedule(schedule_url)
    return parse_schedule(schedule_html)


def get_schedule(schedule_url):
    print('GET {}'.format(schedule_url))
    r = requests.get(schedule_url)
    return r.text


def parse_schedule(schedule_html):
    schedule_data: List[Schedule] = []
    current_year = datetime.now().year

    soup = BeautifulSoup(schedule_html, 'html.parser')

    team_name_group = soup.find_all('span', TEAM_NAME_CLASS)[0]
    team_name_span = team_name_group.find_all('span')[0]
    team_name = team_name_span.text

    schedule_table = soup.find_all('table', SCHEDULE_TABLE_CLASS)[0]
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

    print(team_name)
    pprint(schedule_data)

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


def james() -> tuple[str, Schedule|None]:
    season_id = '21671'  # Example season D
    team_id = '814893'    # Example team ID
    team_name, schedule_data = get_team_data(team_id, season_id)
    next_game = get_next_game_from_schedules(schedule_data)

    return team_name, next_game


def create_roll_call():
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default=BASE_SCHEDULE_URL)
    parser.add_argument('--season-id')
    parser.add_argument('--team-id')
    args = parser.parse_args()

    schedule_url = '{}?{}'.format(args.base_url, urlencode({'seasonid': args.season_id, 'teamid': args.team_id}))

    schedule_html = get_schedule(schedule_url)

    team_name, schedule_data = parse_schedule(schedule_html)

    print(team_name)
    pprint(schedule_data)


if __name__ == '__main__':
    main()
