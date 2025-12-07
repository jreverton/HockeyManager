import discord
import re
import requests
import time
import settings
from guild.models import AttendanceType
from guild import GuildConfig, ChannelConfig, get_guild_config, get_channel_config

from bs4 import BeautifulSoup as bs
from selenium import webdriver


def clear_name(guild: discord.Guild, channel_name: str, user_name: str):
    channel_config: ChannelConfig | None = get_channel_config(guild, channel_name)
    if channel_config is None:
        print(f"clear_name(): Channel config not found for channel: {channel_name}")
        return
    
    attendance_data = channel_config['attendance']
    user_mention = get_name_mention(guild, user_name)

    if user_name in attendance_data[AttendanceType.SKATERS.value]:
        attendance_data[AttendanceType.SKATERS.value].remove(user_name)
    if user_mention in attendance_data[AttendanceType.SKATERS.value]:
        attendance_data[AttendanceType.SKATERS.value].remove(user_mention)

    if user_name in attendance_data[AttendanceType.SUBS.value]:
        attendance_data[AttendanceType.SUBS.value].remove(user_name)
    if user_mention in attendance_data[AttendanceType.SUBS.value]:
        attendance_data[AttendanceType.SUBS.value].remove(user_mention)

    if user_name in attendance_data[AttendanceType.OUT.value]:
        attendance_data[AttendanceType.OUT.value].remove(user_name)
    if user_name in attendance_data[AttendanceType.OUT.value]:
        attendance_data[AttendanceType.OUT.value].remove(user_name)

    if attendance_data[AttendanceType.GOALIE.value] == user_name or attendance_data[AttendanceType.GOALIE.value] == user_mention:
        attendance_data[AttendanceType.GOALIE.value] = ''


def get_name_mention(guild: discord.Guild, user_name: str) -> str:
    member = guild.get_member_named(user_name)
    player = member.mention if member else user_name

    return player


def create_browser():
    options =  webdriver.FirefoxOptions()
    options.add_argument("--headless")
    browser = webdriver.Firefox(options=options)
    return browser


async def create_bot_channels(guild, overwrites) -> int:
    category = await guild.create_category(name="Bot Information Channels", overwrites=overwrites)
    bot_channel = await guild.create_text_channel(
        'manager-bot', topic="Please use bot comands here.", category=category, overwrites=overwrites)

    return bot_channel.id


def create_permissons(owner, role, default):
    return {
        default: discord.PermissionOverwrite(read_messages=False),
        owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role: discord.PermissionOverwrite(read_messages=True, send_messages=True)

    }


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


def get_delayed_info(browser, guild: discord.Guild, channel_name: str):
    guild_config: GuildConfig = get_guild_config(guild)
    channel_config: ChannelConfig | None = get_channel_config(guild, channel_name)
    if channel_config is None:

        # TODO JRE: Should this talk to the channel instead?
        
        print(f"get_delayed_info(): Channel config not found for channel: {channel_name}")
        return

    browser.get(settings.SECONDARY_URL + channel_config['team_id'] + "&seasonid=" + guild_config['season_id'])
    time.sleep(2)
    team_info = browser.page_source
    browser.quit()
    team_info_soup = bs(team_info, "html.parser")
    return team_info_soup


async def get_bot_channel(ctx) -> discord.TextChannel:
    bot_channel = discord.utils.get(ctx.guild.text_channels, name="manager-bot")
    return bot_channel


# TODO JRE: This needs to take a channel name parameter
def get_team_stats(guild: discord.Guild, channel_name: str) -> discord.Embed:
    browser = create_browser()
    team_stats = get_delayed_info(browser, guild, channel_name)
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


def is_alternate(ctx):
    if discord.utils.get(ctx.author.roles, name="Alternate Captain") == None:
        return False
    return True


def is_captain(ctx):
    if discord.utils.get(ctx.author.roles, name="Captain") == None:
        return False
    return True


def pull_player_stats(guild_name, player):
    roster_home_page = bs(requests.get(settings.SECONDARY_URL + settings.SERVER_CONFIG[guild_name]['team_id'] + "&seasonid=" + settings.SERVER_CONFIG[guild_name]['season_id']).text, "html.parser")
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
    team_homepage = bs(requests.get(settings.PRIMARY_URL + settings.SERVER_CONFIG[guild_name]['team_id']+ "&seasonid=" + settings.SERVER_CONFIG[guild_name]['season_id']).text, "html.parser")
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
