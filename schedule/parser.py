import discord
from guild.config import get_guild_config
import requests

from datetime import datetime, timezone
from schedule import Schedule
from typing import List
from guild import ChannelConfig, get_channel_config
import icalendar


BASE_ICS_URL = 'https://api.teams.gamesheet.app/api/public/calendar/teams/{team_calendar_id}/calendar.ics'


"""
Returns team information based upon the team calendar ID and team name.
Retrieves the ICS calendar and parses it into Schedule objects.
"""
def retrieve_team_data(team_calendar_id: str) -> tuple[str, str, List[Schedule]]: # team name, schedule URL, schedule data
    schedule_url = BASE_ICS_URL.format(team_calendar_id=team_calendar_id)
    ics_content = retrieve_ics_schedule(schedule_url)
    
    team_name, schedule_data = parse_ics_schedule(ics_content)
    return team_name, schedule_url, schedule_data


"""
Parses home/away teams from ICS event summary.
Examples:
  "vs Blue Line" -> ("The D.E.N.N.I.S. System", "Blue Line")
  "@ Mean Moose" -> ("Mean Moose", "The D.E.N.N.I.S. System")
Returns tuple of (home_team, away_team)
"""
def parse_teams_from_summary(summary: str, team_name: str) -> tuple[str, str]:
    summary = summary.strip()
    
    if summary.startswith("vs "):
        # Home game: our team is home
        opponent = summary[3:]  # Remove "vs "
        return (team_name, opponent)
    elif summary.startswith("@ "):
        # Away game: opponent is home
        opponent = summary[2:]  # Remove "@ "
        return (opponent, team_name)
    else:
        # Fallback if format is unexpected
        return (team_name, summary)


"""
Returns team name and list of schedules from an ICS calendar content.
Extracts team name from calendar header (X-WR-CALNAME).
Handles timezone conversion to UTC as expected by Schedule model.
"""
def parse_ics_schedule(ics_content: str) -> tuple[str, List[Schedule]]:
    schedule_data: List[Schedule] = []
    team_name: str = ""
    
    try:
        cal = icalendar.Calendar.from_ical(ics_content)
    except Exception as e:
        print(f"Error parsing ICS calendar: {e}")
        return team_name, schedule_data
    
    # Extract team name from calendar header
    team_name = str(cal.get('X-WR-CALNAME', '')).strip()
    if team_name.endswith(' Calendar'):
        team_name = team_name[:-9]  # Remove " Calendar" suffix
    
    if not team_name:
        print("Warning: Could not extract team name from calendar")
    
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        
        try:
            summary = str(component.get('summary', '')).strip()
            location = str(component.get('location', '')).strip()
            dtstart = component.get('dtstart')
            
            if not summary or not dtstart:
                continue
            
            # Extract home and away teams from summary
            home_team, away_team = parse_teams_from_summary(summary, team_name)
            
            # Convert datetime to UTC if it has timezone info
            game_datetime = dtstart.dt
            if isinstance(game_datetime, datetime):
                # If naive, assume UTC
                if game_datetime.tzinfo is None:
                    game_datetime = game_datetime.replace(tzinfo=timezone.utc)
                else:
                    # Convert to UTC
                    game_datetime = game_datetime.astimezone(timezone.utc)
            else:
                # It's a date object, skip it
                continue
            
            schedule_data.append(Schedule(
                home_team=home_team,
                away_team=away_team,
                datetime=game_datetime,
                rink=location,
            ))
        
        except ValueError as e:
            print(f"Error parsing event: {e}")
            continue
    
    return team_name, schedule_data


"""
Retrieves ICS calendar content from the given URL
"""
def retrieve_ics_schedule(ics_url: str) -> str:
    print('GET {}'.format(ics_url))
    r = requests.get(ics_url)
    return r.text

"""
Returns only games after current date
"""
def filter_upcoming_games(schedule_data: List[Schedule]) -> List[Schedule]: # game data
    now = datetime.now(timezone.utc)
    upcoming_games = [game for game in schedule_data if game.datetime > now]
    return upcoming_games


"""
Returns the next game from the list of schedules
"""
def get_next_game_from_schedules(schedule_data: List[Schedule]) -> Schedule|None: # next game data
    upcoming_games = filter_upcoming_games(schedule_data)
    if not upcoming_games:
        return None
    next_game = min(upcoming_games, key=lambda game: game.datetime)
    return next_game


"""
Returns the schedule URL and next game for the guild's configured team.
"""
def get_next_game(guild: discord.Guild, channel_name: str) -> tuple[str, Schedule|None]: # schedule_url, next_game
    # Find the first channel config whose 'name' property equals channel_name
    channel_data: ChannelConfig | None = get_channel_config(guild, channel_name)
    if channel_data is None:
        return "", None

    _, schedule_url, schedule_data = retrieve_team_data(channel_data["team_calendar_id"])
    next_game = get_next_game_from_schedules(schedule_data)

    return schedule_url, next_game
