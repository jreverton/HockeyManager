from pprint import pprint
import discord
import requests
import helper
import settings

from bs4 import BeautifulSoup as bs
from discord.ext import commands
from table2ascii import table2ascii as t2a, Alignment, PresetStyle


async def setup(bot):
    print("Adding team commands to bot")
    bot.add_command(team)

    # Debug: Print command info
    # for cmd in bot.commands:
    #     info = {}
    #     for attr in sorted(a for a in dir(cmd) if not a.startswith('_')):
    #         try:
    #             val = getattr(cmd, attr)
    #             info[attr] = repr(val)
    #         except Exception as e:
    #             info[attr] = f"<Error: {e}>"
    #     pprint({getattr(cmd, "name", repr(cmd)): info})



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
    team_embed = helper.get_team_stats(ctx.guild, ctx.channel.name)
    await ctx.channel.send(embed=team_embed)


@team.command(brief="Pull current team standings")
async def teamStandings(ctx):
    table = get_team_standings(ctx.guild.name)
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


def get_team_standings(guild_name):
    standings_page = bs(requests.get("http://stats.pointstreak.com/players/players-division-standings.html?divisionid=" + settings.SERVER_CONFIG[guild_name]['division_id'] +"&seasonid=" +settings.SERVER_CONFIG[guild_name]['season_id']).text, "html.parser")
    standings_table = standings_page.find_all(class_="table table-hover table-striped nova-stats-table")[0].find_all("tr")
    standings_table = standings_table[1:]
    cell_data = format_page_data(standings_table)
    return cell_data


def format_page_data(data):
    rows= []
    i = 0
    for row in data:
        temp = []
        for cell in row.contents:
            if cell.text == '' or cell.text== '\n' or cell.text == "\t" or cell.text == " ":
                continue
            else:
                if i%14 == 13:
                    temp.append(cell.text.replace("\t", '').replace("\n", ''))
                    rows.append(temp)
                    i = i + 1
                    temp=[]
                elif i%14 == 0:
                    temp.append(cell.text.replace("\t", '').replace("\n", '')[1:])
                    i = i + 1
                else:
                    temp.append(cell.text.replace("\t", '').replace("\n", ''))
                    i = i + 1
    return rows
