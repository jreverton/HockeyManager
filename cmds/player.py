import re
import discord
import requests
from guild.config import get_channel_config, get_guild_config
from guild.models import ChannelConfig, GuildConfig
import settings
from discord.ext import commands


PLAYER_STANDINGS_API_URL = 'https://gamesheetstats.com/api/useTeamRoster/getPlayerStandings/{season_id}/players/{gs_team_id}'


# Sets up the player commands
async def setup(bot):
    print("Adding player commands to bot")
    bot.add_command(player)


@commands.group(brief="Player commands")
async def player(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("A subcommand was not passed")


@player.command(brief="Pull the available stats for the specified player")
async def stats(ctx, *, player_name: str):
    player_name = player_name.lower().title()
    stat_embed = await pull_player_stats(ctx.guild, ctx.channel, player_name)
    if type(stat_embed) == discord.embeds.Embed:
        await ctx.channel.send(embed=stat_embed)
    else:
        await ctx.channel.send(stat_embed)


@stats.error
async def stats_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify a player name.")
    raise error


async def pull_player_stats(guild: discord.Guild, channel: discord.TextChannel, player_name: str):
    guild_config: GuildConfig = get_guild_config(guild)
    channel_config: ChannelConfig | None = get_channel_config(guild, channel.name)
    if channel_config is None:
        await channel.send("Channel configuration not found.")
        return

    url = PLAYER_STANDINGS_API_URL.format(season_id=guild_config['season_id'], gs_team_id=channel_config['gs_team_id'])
    params = {
        'filter[limit]': 100,
        'filter[offset]': 0,
        'filter[sort]': '-pts'
    }
    response = requests.get(url, params=params, timeout=20)
    if response.status_code != 200:
        return "Unable to retrieve player stats from GameSheet API."

    data = response.json()
    player_data = data.get('playerData', {})
    goalie_data = data.get('goalieData', {})

    normalized_query = player_name.strip().lower()
    player_index = None
    player_title = None
    is_goalie = False

    for index, player in enumerate(player_data.get('names', [])):
        title = player.get('title', '')
        if normalized_query in title.lower():
            player_index = index
            player_title = title
            break

    if player_index is None:
        for index, goalie in enumerate(goalie_data.get('names', [])):
            title = goalie.get('title', '')
            if normalized_query in title.lower():
                player_index = index
                player_title = title
                is_goalie = True
                break

    if player_index is None:
        return f"No player found matching '{player_name}'."

    stat_embed = discord.Embed(
        color=discord.Color.blue(),
        title=f"{player_title}"
    )

    if is_goalie:
        metrics = [
            ('Games Played', 'gp'),
            ('Games Started', 'gs'),
            ('Minutes', 'min'),
            ('Wins', 'wins'),
            ('Losses', 'losses'),
            ('Ties', 'ties'),
            ('Overtime Losses', 'otl'),
            ('Shots Against', 'sa'),
            ('Goals Against', 'ga'),
            ('Goals Against Avg', 'gaa'),
            ('Saves', 'svPct'),
            ('Save %', 'svPct'),
            ('Power Play GA', 'ppga'),
            ('Short Handed GA', 'shga'),
            ('Shutouts', 'so'),
            ('Penalty Minutes', 'pim')
        ]
        for label, key in metrics:
            values = goalie_data.get(key, [])
            stat_embed.add_field(name=label, value=str(values[player_index] if player_index < len(values) else 'N/A'))
    else:
        metrics = [
            ('Jersey', 'jersey'),
            ('Position', 'positions'),
            ('Games Played', 'gp'),
            ('Goals', 'g'),
            ('Assists', 'a'),
            ('Points', 'pts'),
            ('Power Play Goals', 'ppg'),
            ('Power Play Assists', 'ppa'),
            ('Short Handed Goals', 'shg'),
            ('Short Handed Assists', 'sha'),
            ('Game Winning Goals', 'gwg'),
            ('Points Per Game', 'ptspg'),
            ('Penalty Minutes', 'pim'),
            ('Shots on Goal', 'sog'),
            ('Shots', 'shots')
        ]
        for label, key in metrics:
            values = player_data.get(key, [])
            value = values[player_index] if player_index < len(values) else 'N/A'
            if isinstance(value, list):
                value = ', '.join(str(x) for x in value)
            stat_embed.add_field(name=label, value=str(value))

    return stat_embed



