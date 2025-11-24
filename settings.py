import os

from dotenv import find_dotenv, load_dotenv, set_key
from pathlib import Path
from typing import NewType, Optional

from enum import Enum

dotenv_file = find_dotenv()
load_dotenv(dotenv_file)

# GET DISCORD BOT TOKEN
# DISCORD_API_SECRET = os.getenv("DISCORD_TOKEN")
Token = NewType("Token", str)
DISCORD_API_SECRET: Optional[Token] = (
    Token(os.getenv("DEV_DISCORD_TOKEN")) if os.getenv("DEV_DISCORD_TOKEN") else None # type: ignore
)

# DIRECTORIES
BASE_DIR = Path(__file__).parent
CMDS_DIR = BASE_DIR / "cmds"
TASKS_DIR = BASE_DIR / "tasks"
DATA_DIR = BASE_DIR / "data"

# PRIMARY URL
PRIMARY_URL = "http://stats.pointstreak.com/players/players-team-schedule.html?teamid="
SECONDARY_URL = 'http://stats.pointstreak.com/players/players-team-roster.html?teamid='

# SERVER CONFIG
SERVER_CONFIG = {}

# PLAYER TYPE
class AttendanceType(str, Enum):
    SKATERS = "Skaters"
    SUBS = "Subs"
    GOALIE = "Goalie"
    OUT = "Out"

# STATS DICTIONARY
PLAYER_STAT_DICT = {
    1: "Number",
    3: "Name",
    5: "Games Played",
    7: "Goals",
    9: "Assist",
    11: "Points",
    13: "Penalty Minutes",
    15: "Power Play Goals",
    17: "Short Handed Goals",
    19: "Game Winning Goals",
    21: "Power Play Goals Against"
}

GOALIE_STAT_DICT = {
    1: "Number",
    3: "Name",
    5: "Games Played (G)",
    7: "Minutes",
    9: "Wins",
    11: "Loses",
    12: "Ties",
    14: "Shoot Outs",
    16: "Goals Against",
    18: "Goals Against Average",
    20: "Saves",
    22: "Save Percentage"
}

# TABLE HEADER
HEADER = [
    "Team Name", 
    "GP", 
    "W", 
    "L", 
    "OTW", 
    "SOW", 
    "OTL", 
    "SOL", 
    "PTS", 
    "GF", 
    "GA", 
    "PIM", 
    "Last 5", 
    "Streak"
]