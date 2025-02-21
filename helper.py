import discord
import json
import re
import requests
import time
import settings

from bs4 import BeautifulSoup as bs
from selenium import webdriver

def clear_name(guild_name, user):
    if user in settings.SERVER_CONFIG[guild_name]['attendance']['Forwards']:
        settings.SERVER_CONFIG[guild_name]['attendance']['Forwards'].remove(user)

    if user in settings.SERVER_CONFIG[guild_name]['attendance']['Defense']:
        settings.SERVER_CONFIG[guild_name]['attendance']['Defense'].remove(user)

    if user in settings.SERVER_CONFIG[guild_name]['attendance']['Maybe']:
        settings.SERVER_CONFIG[guild_name]['attendance']['Maybe'].remove(user)

    if settings.SERVER_CONFIG[guild_name]['attendance']['Goalie'] == user:
        settings.SERVER_CONFIG[guild_name]['attendance']['Goalie'] = ''

    if user in settings.SERVER_CONFIG[guild_name]['attendance']['Out']:
        settings.SERVER_CONFIG[guild_name]['attendance']['Out'].remove(user)

def create_browser():
    options =  webdriver.FirefoxOptions()
    options.add_argument("--headless")
    browser = webdriver.Firefox(options=options)
    return browser

async def create_bot_channels(guild, overwrites):
    category = await guild.create_category(name="Bot Information Channels", overwrites=overwrites)
    bot_channel = await guild.create_text_channel('bot-commands',topic="please use bot comands here.", category=category, overwrites=overwrites)

    return bot_channel.id

def create_permissons(owner, role, default):
    return {
        default: discord.PermissionOverwrite(read_messages=False),
        owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role: discord.PermissionOverwrite(read_messages=True, send_messages=True)

    }

def create_server_config(data_dict, name, id):
    data_dict['attendance']= {
        "Forwards": [],
        "Defense": [],
        "Maybe": [],
        "Goalie": "",
        "Out": []
    }    
    data_dict['bot_channel'] = 0
    data_dict['file_prefix'] = name.replace(" ", "")
    data_dict['id'] = id
    data_dict['TeamID'] = 0
    data_dict['SeasonID'] = 0
    data_dict["DivID"] = 0

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

def format_team_info(tags):
    team_ranks = tags.find_all(class_="nova-team-rank")
    team_stats_v_div = tags.find_all(class_="morris-hover morris-default-style")
    ranks = {}
    stats = {}

    for tag in team_ranks:
        label = tag.find(class_="nova-team-rank__label").text
        rank = tag.find(class_="nova-team-rank__ranking").text
        value = tag.find(class_="text-center").text[1:-1]
        ranks[label] = [rank, value]

    for tag in team_stats_v_div:
        stats[tag.find(class_="morris-hover-row-label").text] = [
            tag.find_all(class_="morris-hover-point")[0].text.replace("\t", '').replace("\n", '').split(" ")[-1],
            tag.find_all(class_="morris-hover-point")[1].text.replace("\t", '').replace("\n", '').split(" ")[-1]
        ]
    
    return ranks, stats

def get_delayed_info(browser, guild_name):
    browser.get(settings.SECONDARY_URL + settings.SERVER_CONFIG[guild_name]['TeamID'] + "&seasonid=" + settings.SERVER_CONFIG[guild_name]['SeasonID'])
    time.sleep(2)
    team_info = browser.page_source
    browser.quit()
    team_info_soup = bs(team_info, "html.parser")
    return team_info_soup

async def get_bot_channel(ctx):
    bot_channel = discord.utils.get(ctx.guild.channels, name="bot-commands")
    return bot_channel

def get_team_standings(guild_name):
    standings_page = bs(requests.get("http://stats.pointstreak.com/players/players-division-standings.html?divisionid=" + settings.SERVER_CONFIG[guild_name]['DivID'] +"&seasonid=" +settings.SERVER_CONFIG[guild_name]['SeasonID']).text, "html.parser")
    standings_table = standings_page.find_all(class_="table table-hover table-striped nova-stats-table")[0].find_all("tr")
    standings_table = standings_table[1:]
    cell_data = format_page_data(standings_table)
    return cell_data

def get_team_stats(guild_name):
    browser = create_browser()
    team_stats = get_delayed_info(browser, guild_name)
    ranks, stats =  format_team_info(team_stats)

    team_stat_embed = discord.Embed(
        title="Team Stats",
        color=discord.Color.dark_grey()
    )

    for key in ranks.keys():
        team_stat_embed.add_field(
            name=key,
            value=f"> Place: {ranks[key][0]}\n> Team: {ranks[key][1]}"
        )
    
    for key in stats.keys():
        team_stat_embed.add_field(
            name=key,
            value=f"> Team: {stats[key][0]}\n> Division Avg: {stats[key][1]}"
        )

    return team_stat_embed

def is_admin(ctx):
    '''
        Command Control function: isAdmin
        Desc:
            Check function used for security control over commands.
            Checks for the admin role on the user who called it
        parameter:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
    '''
    # check if admin role is in the user's role list. If not there return false
    if discord.utils.get(ctx.author.roles, name="Admin") == None:
        return False
    return True

def is_assitant(ctx):
    if discord.utils.get(ctx.author.roles, name="Assistant Captain") == None:
        return False
    return True

def is_captain(ctx):
    if discord.utils.get(ctx.author.roles, name="Captain") == None:
        return False
    return True

def lineup_embed(guild_name):
    lineup_embed = discord.Embed(
        color=discord.Color.brand_red(),
        title="Current Line Up"
    )

    forward_lineup = ""
    defense_lineup = ""
    maybe_lineup = ""
    out_lineup = ""

    if settings.SERVER_CONFIG[guild_name]['attendance']['Goalie'] == "":
        goalie_name = ""
    else:
        goalie_name = f"> {settings.SERVER_CONFIG[guild_name]['attendance']['Goalie']}"

    for value in settings.SERVER_CONFIG[guild_name]['attendance']['Forwards']:
        forward_lineup = forward_lineup + f"> {value}\n"

    for value in settings.SERVER_CONFIG[guild_name]['attendance']['Defense']:
        defense_lineup = defense_lineup + f"> {value}\n"
    
    for value in settings.SERVER_CONFIG[guild_name]['attendance']['Maybe']:
        maybe_lineup = maybe_lineup + f"> {value}\n"

    for value in settings.SERVER_CONFIG[guild_name]['attendance']['Out']:
        out_lineup = out_lineup + f"> {value}\n"

    lineup_embed.add_field(
        name="Forwards:",
        value=forward_lineup,
        inline=False
    )

    lineup_embed.add_field(
        name="Defense:",
        value=defense_lineup,
        inline=False
    )

    lineup_embed.add_field(
        name="Maybe:",
        value=maybe_lineup,
        inline=False
    )

    lineup_embed.add_field(
        name="Goalie:",
        value=goalie_name,
        inline=False
    )

    lineup_embed.add_field(
        name="Out:",
        value=out_lineup,
        inline=False
    )

    return lineup_embed

def pull_player_stats(guild_name, player):
    roster_home_page = bs(requests.get(settings.SECONDARY_URL + settings.SERVER_CONFIG[guild_name]['TeamID'] + "&seasonid=" + settings.SERVER_CONFIG[guild_name]['SeasonID']).text, "html.parser")
    player_stats = roster_home_page.find_all("a", string=re.compile(player))
    if len(player_stats) == 3:
        player_stats.pop(1)
    if player_stats != []:
        player_row = player_stats[0].parent.parent
        stat_embed = discord.Embed(
                color=discord.Color.blue(),
                title=f'# {player_row.contents[1].get_text(strip=True)}    {player}'
            )
        secondary = False
        for tag in player_stats:
            player_row = tag.parent.parent
            if not secondary:
                for i in range(len(player_row.contents)):
                    if i < 4:
                        continue
                    else:
                        if player_row.contents[i].get_text(strip=True) != '':
                            stat_embed.add_field(
                                name=settings.PLAYER_STAT_DICT[i],
                                value=player_row.contents[i].get_text(strip=True)
                            )
                secondary = True
            else:
                for i in range(len(player_row.contents)):
                    if i < 3:
                        stat_embed.add_field(
                            name=" ",
                            value=" "
                        )
                    elif 3 <= i < 4:
                        continue
                    else:
                        if player_row.contents[i].get_text(strip=True) != '':
                            stat_embed.add_field(
                                name=settings.GOALIE_STAT_DICT[i],
                                value=player_row.contents[i].get_text(strip=True)
                        )
        return stat_embed
    else:
        return " No name found"

def pull_schedule(guild_name):
    team_homepage = bs(requests.get(settings.PRIMARY_URL + settings.SERVER_CONFIG[guild_name]['TeamID']+ "&seasonid=" + settings.SERVER_CONFIG[guild_name]['SeasonID']).text, "html.parser")
    schedule_table = team_homepage.find(class_="table-responsive")
    schedule_games = schedule_table.findAll("tr")

    home_teams = []
    away_teams = []
    game_day = []
    game_time = []

    for row in schedule_games:
        data = row.findAll("td")
        index =0
        for cell in data:
            team = cell.find("a")
            
            if index == 0:
                home_teams.append(team.text)
            elif index == 1:
                away_teams.append(team.text)
            elif index == 2:
                game_day.append(cell.text)
            elif index == 3:
                game_time.append(cell.text)
            index = index + 1

    return home_teams, away_teams, game_day, game_time

def save_config(ctx):
    # create the file name
    file_name = settings.DATA_DIR / (settings.SERVER_CONFIG[ctx.guild.name]['file_prefix'] + '_config.json')

    # save to the file
    with open(file_name, 'w') as cur_config:
        json.dump(settings.SERVER_CONFIG[ctx.guild.name],cur_config)
        
async def send_line_up(guild_name, user, position, channel, msg):
    if position != 'Goalie':
        settings.SERVER_CONFIG[guild_name]['attendance'][position].append(user)
    else:
        settings.SERVER_CONFIG[guild_name]['attendance']['Goalie'] = user
    lineup = lineup_embed(guild_name)
    if msg:
        await msg.edit(embed=lineup)
    else:
        msg = await channel.send(embed=lineup)
        return msg.id