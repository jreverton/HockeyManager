# EDMManager Bot

## Startup

From the repository root, activate the virtual environment and run:

```bash
source .venv/Scripts/activate
python main.py
```

The bot uses `!` as the command prefix.

## Discord Commands

### General
- `!rollcall`
  - Triggers the temporary roll call task for the current guild.

### `!config` group
- `!config changeFilePrefix <newPrefix>`
  - Change the saved config file prefix for the server.
  - Deletes old saved files that use the previous prefix.
- `!config list`
  - Shows the currently loaded server configuration.
- `!config load`
  - Loads the server config from a JSON file in `data/`.
- `!config save`
  - Saves the current server config to a JSON file in `data/`.

### `!admin` group
- `!admin adhocAttendance`
  - Sends an attendance prompt for an upcoming game using schedule data.
- `!admin checkSeasonId`
  - Shows the current `season_id` from the guild config.
- `!admin checkTeamId`
  - Shows the current channel `gs_team_id` and `team_calendar_id`.
- `!admin clear [channel] [amount] [month] [day] [year]`
  - Deletes messages from a channel.
  - If `channel` is omitted or `-`, it uses the current channel.
  - If `amount` is omitted or `-`, the purge runs without a count limit.
  - Optional date parameters filter messages before that date.
- `!admin newSeason <id>`
  - Updates the guild `season_id` used by GameSheet API URLs.
- `!admin newTeam <id>`
  - Updates the current channel `gs_team_id` used by GameSheet stats APIs.
- `!admin newTeamCalendarId <id>`
  - Updates the current channel `team_calendar_id` used by schedule/calendar API.
- `!admin sendSchedule`
  - Sends the team schedule embed into the `📆schedule` channel.

### `!player` group
- `!player stats <player_name>`
  - Fetches player stats from GameSheet for the current channel team.

### `!team` group
- `!team stats`
  - Fetches team stats and divisional comparison from GameSheet.
- `!team standings`
  - Fetches current division standings and prints a table.

## Configuration Notes

- The bot loads server configuration from JSON files in `data/`.
- Config fields include `season_id`, `gs_team_id`, `team_calendar_id`, and `division_id`.
- `team_calendar_id` is used for schedule/calendar ICS URLs.
- `gs_team_id` is used for GameSheet team stat and player endpoints.

## Useful paths

- `main.py` — bot entry point
- `cmds/config.py` — config load/save commands
- `cmds/admin.py` — admin commands and config updates
- `cmds/team.py` — team stat and standings commands
- `cmds/player.py` — player stats command
- `schedule/parser.py` — schedule/calendar parsing logic
- `data/` — stored JSON config files
