import discord
import requests
from guild.config import get_channel_config, get_guild_config
from guild.models import ChannelConfig, GuildConfig
import settings
from discord.ext import commands
from table2ascii import table2ascii as t2a, Alignment, PresetStyle

TEAM_DATA_API_URL = "https://gamesheetstats.com/api/useTeamData/{season_id}/{gs_team_id}"
DIVISION_STANDINGS_API_URL = "https://gamesheetstats.com/api/useStandings/getDivisionStandings/{season_id}"

async def setup(bot):
    print("Adding team commands to bot")
    bot.add_command(team)


@commands.group(brief="Team commands")
async def team(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("A subcommand was not passed")


@team.command(brief="Gather team stats, and divisional comparison stats")
async def stats(ctx):
    await ctx.channel.send("One moment please...")
    team_embed = await get_team_stats(ctx.guild, ctx.channel)
    if team_embed is not None:
        await ctx.channel.send(embed=team_embed)


async def get_team_stats(guild: discord.Guild, channel: discord.TextChannel) -> discord.Embed | None:
    guild_config: GuildConfig = get_guild_config(guild)
    channel_config: ChannelConfig | None = get_channel_config(guild, channel.name)
    if channel_config is None:
        await channel.send("Channel configuration not found.")
        return

    team_data = fetch_team_data(guild_config['season_id'], channel_config['gs_team_id'])
    if team_data is None:
        await channel.send("Unable to retrieve team stats from GameSheet API.")
        return

    team_stat_embed = discord.Embed(
        title="Team Stats",
        description=team_data.get('title', 'Team information'),
        color=discord.Color.dark_grey()
    )

    if team_data.get('logoUrl'):
        team_stat_embed.set_thumbnail(url=team_data['logoUrl'])

    team_stat_embed.add_field(name="Record", value=team_data.get('record', 'N/A'), inline=True)
    team_stat_embed.add_field(name="Rank", value=str(team_data.get('rank', 'N/A')), inline=True)
    team_stat_embed.add_field(name="PTS", value=str(team_data.get('pts', 'N/A')), inline=True)
    team_stat_embed.add_field(name="Division", value=team_data.get('division', {}).get('title', 'N/A'), inline=True)
    team_stat_embed.add_field(name="Season", value=team_data.get('seasonTitle', 'N/A'), inline=False)
    team_stat_embed.add_field(name="Association", value=team_data.get('associationTitle', 'N/A'), inline=False)

    return team_stat_embed


def fetch_team_data(season_id: int, gs_team_id: int) -> dict | None:
    url = TEAM_DATA_API_URL.format(season_id=season_id, gs_team_id=gs_team_id)
    response = requests.get(f"{url}?gametype=overall", timeout=20)
    if response.status_code != 200:
        return None
    data = response.json()
    return data.get('data') if isinstance(data, dict) else None


def fetch_division_standings(season_id: int, gs_division_id: int) -> list | None:
    url = DIVISION_STANDINGS_API_URL.format(season_id=season_id)
    params = {
        'filter[divisionId]': gs_division_id,
        'filter[type]': 'division',
        'filter[gameType]': 'overall',
        'filter[limit]': 100,
        'filter[offset]': 0,
        'filter[sort]': '-rank'
    }
    response = requests.get(url, params=params, timeout=20)
    if response.status_code != 200:
        return None
    data = response.json()
    return data if isinstance(data, list) else None


@team.command(brief="Pull current team standings")
async def standings(ctx):
    table = await get_team_standings(ctx.guild, ctx.channel)
    if not table:
        return
    output = t2a(
        header=settings.STANDINGS_HEADER,
        body=table,
        first_col_heading=True,
        style=PresetStyle.thin_compact,
        alignments=[
            Alignment.LEFT,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
            Alignment.CENTER,
        ]
    )
    await ctx.send(f"```\n{output}\n```")


async def get_team_standings(guild: discord.Guild, channel: discord.TextChannel):
    guild_config: GuildConfig = get_guild_config(guild)
    channel_config: ChannelConfig | None = get_channel_config(guild, channel.name)
    if channel_config is None:
        await channel.send("Channel configuration not found.")
        return
    team_data = fetch_team_data(guild_config['season_id'], channel_config['gs_team_id'])
    if team_data is None:
        await channel.send("Unable to retrieve team division information.")
        return []

    gs_division_id = team_data.get('division', {}).get('id')
    if not gs_division_id:
        await channel.send("Unable to determine team division.")
        return []

    standings = fetch_division_standings(guild_config['season_id'], gs_division_id)
    if standings is None:
        await channel.send("Unable to retrieve division standings.")
        return []

    standings_group = None
    gs_team_id = channel_config['gs_team_id']
    for group in standings:
        table_data = group.get('tableData', {})
        if gs_team_id in table_data.get('teamIds', []):
            standings_group = table_data
            break

    if standings_group is None:
        await channel.send("Team not found in division standings.")
        return []

    rows = []
    titles = standings_group.get('teamTitles', [])
    for index, team in enumerate(titles):
        rows.append([
            team.get('title', 'N/A'),
            str(standings_group.get('gp', [])[index] if index < len(standings_group.get('gp', [])) else 'N/A'),
            str(standings_group.get('w', [])[index] if index < len(standings_group.get('w', [])) else 'N/A'),
            str(standings_group.get('l', [])[index] if index < len(standings_group.get('l', [])) else 'N/A'),
            str(standings_group.get('otl', [])[index] if index < len(standings_group.get('otl', [])) else 'N/A'),
            str(standings_group.get('sol', [])[index] if index < len(standings_group.get('sol', [])) else 'N/A'),
            str(standings_group.get('pts', [])[index] if index < len(standings_group.get('pts', [])) else 'N/A'),
            str(standings_group.get('gf', [])[index] if index < len(standings_group.get('gf', [])) else 'N/A'),
            str(standings_group.get('ga', [])[index] if index < len(standings_group.get('ga', [])) else 'N/A'),
            str(standings_group.get('pim', [])[index] if index < len(standings_group.get('pim', [])) else 'N/A'),
            str(standings_group.get('p10', [])[index] if index < len(standings_group.get('p10', [])) else 'N/A'),
            str(standings_group.get('stk', [])[index] if index < len(standings_group.get('stk', [])) else 'N/A'),
        ])

    # Sort rows by PTS (column index 6) descending. Non-integer or 'N/A' values are treated as 0.
    def _pts_key(row):
        try:
            return int(row[6])
        except Exception:
            try:
                return int(float(row[6]))
            except Exception:
                return 0

    rows.sort(key=_pts_key, reverse=True)

    return rows


