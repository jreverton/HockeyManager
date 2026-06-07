import discord
import requests
import settings
from guild.models import AttendanceType
from guild import ChannelConfig, get_channel_config
from schedule.parser import retrieve_team_data

from bs4 import BeautifulSoup as bs
from selenium import webdriver


def clear_name(guild: discord.Guild, channel_name: str, user_name: str):
    channel_config: ChannelConfig | None = get_channel_config(guild, channel_name)
    if channel_config is None:
        # Channel config not found, so name is cleared by default
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
    if user_mention in attendance_data[AttendanceType.OUT.value]:
        attendance_data[AttendanceType.OUT.value].remove(user_mention)

    if attendance_data[AttendanceType.GOALIE.value] == user_name or attendance_data[AttendanceType.GOALIE.value] == user_mention:
        attendance_data[AttendanceType.GOALIE.value] = ''


def get_name_mention(guild: discord.Guild, user_name: str) -> str:
    member = guild.get_member_named(user_name)
    player = member.mention if member else user_name

    return player


def create_browser() -> webdriver.Firefox:
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


async def get_bot_channel(ctx) -> discord.TextChannel:
    bot_channel = discord.utils.get(ctx.guild.text_channels, name="manager-bot")
    return bot_channel


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


def pull_schedule(guild_name):
    guild_config = settings.SERVER_CONFIG.get(guild_name, {})
    channels = guild_config.get("channels", [])

    team_calendar_id = ""
    for channel in channels:
        if channel.get("team_calendar_id") and channel.get("team_calendar_id") != "0":
            team_calendar_id = channel["team_calendar_id"]
            break

    if not team_calendar_id:
        return [], [], [], []

    _, _, schedule_data = retrieve_team_data(team_calendar_id)

    home_teams = [game.home_team for game in schedule_data]
    away_teams = [game.away_team for game in schedule_data]
    game_day = [game.datetime.strftime("%a, %b %d") for game in schedule_data]
    game_time = [game.datetime.strftime("%I:%M %p").lstrip("0") for game in schedule_data]

    return home_teams, away_teams, game_day, game_time
