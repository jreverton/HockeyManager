import os

from dotenv import find_dotenv, load_dotenv
from pathlib import Path
from typing import NewType, Optional

from guild import ServerConfigDict

dotenv_file = find_dotenv()
load_dotenv(dotenv_file)

# GET DISCORD BOT TOKEN
Token = NewType("Token", str)
DISCORD_API_SECRET: Optional[Token] = (
    Token(os.getenv("DISCORD_TOKEN")) if os.getenv("DISCORD_TOKEN") else None # type: ignore
)

# DIRECTORIES
BASE_DIR = Path(__file__).parent
CMDS_DIR = BASE_DIR / "cmds"
TASKS_DIR = BASE_DIR / "tasks"
DATA_DIR = BASE_DIR / "data"

# SERVER CONFIG
SERVER_CONFIG: ServerConfigDict = {}

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
    21: "Points-Per-Game Average"
}

GOALIE_STAT_DICT = {
    1: "Number",
    3: "Name",
    5: "Games Played (G)",
    7: "Minutes",
    9: "Wins",
    11: "Losses",
    12: "Ties",
    14: "Shoot Outs",
    16: "Goals Against",
    18: "Goals Against Average",
    20: "Saves",
    22: "Save Percentage"
}

# TABLE HEADER
STANDINGS_HEADER = [
    "Team Name",
    "GP",
    "W",
    "L",
    "OTL",
    "SOL",
    "PTS",
    "GF",
    "GA",
    "PIM",
    "Last 5",
    "Streak",
]