import discord
import helper
import settings

from bs4 import BeautifulSoup as bs
from discord.ext import commands
from table2ascii import table2ascii as t2a, Alignment, PresetStyle

@commands.group(brief="Team commands")
async def team(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("A subcommand was not passed")

@team.command(brief="Pull the available stats for the specified player")
async def myStats(ctx, *, player):
    player = player.lower().title()
    stat_embed = helper.pull_player_stats(ctx.guild.name, player)
    if type(stat_embed) == discord.embeds.Embed:
        await ctx.channel.send(embed=stat_embed)
    else:
        await ctx.channel.send(stat_embed)

@team.command(brief="Gather team stats, and divisional comparison stats")
async def teamStats(ctx):
    await ctx.channel.send("One moment please...")
    team_embed = helper.get_team_stats(ctx.guild.name)
    await ctx.channel.send(embed=team_embed)

@team.command(brief="Pull current team standings")
async def teamStandings(ctx):
    table = helper.get_team_standings(ctx.guild.name)
    output = t2a(
        header=settings.HEADER,
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
            Alignment.CENTER, 
            Alignment.CENTER
        ]
    )
    await ctx.send(f"```\n{output}\n```")


async def setup(bot):
    print("Adding team commands to bot")
    bot.add_command(team)