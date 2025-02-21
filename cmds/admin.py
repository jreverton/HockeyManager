import discord
import helper
import settings
import views

from datetime import datetime, timedelta
from discord.ext import commands

@commands.group(brief="Bot controls for current server")
async def admin(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("A subcommand was not passed")

@admin.command(brief="Send attendance in case of an error")
async def adhocAttendance(ctx):
    current_year = str(datetime.today().year)
    today_date =datetime.today().date()
    four_days_later = datetime.today().date() + timedelta(days=4)
    
    # Swap the below code for testing in the devserver
    # team_guild = discord.utils.get(bot.guilds, name='dev server 2')
    team_guild = ctx.guild

    tata =  discord.utils.get(team_guild.roles, name="Tata")
    attendance_channel = discord.utils.get(team_guild.channels, name="📤-📥-attendance")
    home_teams, away_teams, game_days, game_times = helper.pull_schedule(team_guild.name)
    bye_week = False

    for i in range(len(game_days)):
        game_date = datetime.strptime(game_days[i] + " " + current_year, "%a, %b %d %Y").date()
        if today_date <= game_date< four_days_later:
            gametime_embed = discord.Embed(
                color=discord.Color.brand_green(),
                title="Next Game"
            )
            gametime_embed.add_field(name="Date:", value=game_days[i], inline=False)
            gametime_embed.add_field(name="Time:", value=game_times[i], inline=False)
            gametime_embed.add_field(name="Home Team:", value=home_teams[i], inline=False)
            gametime_embed.add_field(name="Away Team:", value=away_teams[i], inline=False)
            rollcall_view = views.RollCallView(datetime.now()) 
            await attendance_channel.send(embed=gametime_embed)
            await attendance_channel.send(f"{tata.mention} Alright boys, who is in?", view=rollcall_view)
            break
        elif i == len(game_days) - 1:
            bye_week = True

    if bye_week:
        await attendance_channel.send(f"{tata.mention} No game this week boys! Have a good weekend!")
        bye_week = False

@admin.command(brief="Check the current season id")
@commands.check(helper.is_admin)
async def checkDivId(ctx):
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send(f"Current Season id: {settings.SERVER_CONFIG[ctx.guild.name]['DivID']}")

@admin.command(brief="Check the current season id")
@commands.check(helper.is_admin)
async def checkSeasonId(ctx):
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send(f"Current Season id: {settings.SERVER_CONFIG[ctx.guild.name]['SeasonID']}")

@admin.command(brief="Check the current team id")
@commands.check(helper.is_admin)
async def checkTeamId(ctx):
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send(f"Current Team id: {settings.SERVER_CONFIG[ctx.guild.name]['TeamID']}")

@admin.command(brief="delete messages")
@commands.check(helper.is_admin)
async def clear(ctx, channel: str = None, amount=None, month=None, day= None, year=None):
    '''
        Command: clear
        desc:
            Take in an amount and date pieces and delete the specified
            number of messages from the channel. for any value enter '-'
            that you do not want to provide. There is a limit based on rate limiting.
            This can vary based on number of message and the history of the 
            channel
        parameter:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
            channel - String, Channel to clear messages from
            amount - anytype (will be entered as a string), amound of messages to purge
            month - anytype (will be entered as a string), month poriton of the date
            day - anytype (will be entered as a string), day portion of the date
            year - anytype (will be entered as a string), year portion of the date
    '''
    # getting the bot channel
    bot_channel = await helper.get_bot_channel(ctx)

    if amount == '-' or amount == None:
        # amount was not specified
        amount = None
    else:
        # converting the strign to an int and accounting for 0 indexing
        amount = int(amount) + 1
    
    if (month == None or month == '-') or (day == None or day == "-") or (year == None or year == '-'):
        # make the date none if a piece of the date is mising
        date = None
    else:
        # create a date value
        date  =  datetime(int(year), int(month), int(day))

    # get the channel to delete messages from
    if not (channel == "-" or channel == None):
        channel_choice = discord.utils.get(ctx.guild.channels, name=channel)
    else:
        channel_choice = ctx.channel

    # delete the message prior to the given date
    message_list = await channel_choice.purge(limit=amount, before=date)

    # let admin know the result
    await bot_channel.send(f"{len(message_list)} were deleted.")

@admin.command(brief="Change Team ID")
@commands.check(helper.is_admin)
async def newDiv(ctx, id):
    '''
        Command: newDiv
        desc:
            Update the Division id that pointstreak has used.
            This id can be obtained from the url of the
            schedule for the current season and team
        parameters:
            id - team id from pointsteak url
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
    '''
    # getting the bot channel
    bot_channel = await helper.get_bot_channel(ctx)

    old_team_id = settings.SERVER_CONFIG[ctx.guild.name]['DivID']
    settings.SERVER_CONFIG[ctx.guild.name]['DivID'] = id
    
    await bot_channel.send(f"Team Id Updated. Previous id: {old_team_id}; New team id: {id}")

@admin.command(brief="Change Season ID")
@commands.check(helper.is_admin)
async def newSeason(ctx, id):
    '''
        Command: newSeason
        desc:
            Update the season id that pointstreak has used.
            This id can be obtained from the url of the
            schedule for the current season and team
        parameters:
            id - season id from pointsteak url
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
    '''
    # getting the bot channel  
    bot_channel = await helper.get_bot_channel(ctx)

    old_season_id = settings.SERVER_CONFIG[ctx.guild.name]['SeasonID']   
    settings.SERVER_CONFIG[ctx.guild.name]['SeasonID'] = id
    
    await bot_channel.send(f"Season Id Updated. Previous id: {old_season_id}; New Season Id: {id}")

@admin.command(brief="Change Team ID")
@commands.check(helper.is_admin)
async def newTeam(ctx, id):
    '''
        Command: newTeam
        desc:
            Update the team id that pointstreak has used.
            This id can be obtained from the url of the
            schedule for the current season and team
        parameters:
            id - team id from pointsteak url
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
    '''
    # getting the bot channel
    bot_channel = await helper.get_bot_channel(ctx)

    old_team_id = settings.SERVER_CONFIG[ctx.guild.name]['TeamID']
    settings.SERVER_CONFIG[ctx.guild.name]['TeamID'] = id
    
    await bot_channel.send(f"Team Id Updated. Previous id: {old_team_id}; New team id: {id}")

@admin.command(brief="Send team schedule")
@commands.check(helper.is_admin)
async def sendSchedule(ctx):
    schedule_channel = discord.utils.get(ctx.guild.channels, name="📆schedule")
    schedule_embed = discord.Embed(
        color=discord.Color.brand_green(),
        title="Team Schedule"
    )

    home_teams, away_teams, game_days, game_times = helper.pull_schedule(ctx.guild.name)

    for i in range(len(game_days)):
        if i == 24:
            await schedule_channel.send(embed=schedule_embed)
            schedule_embed.clear_fields()
            schedule_embed.add_field(
                name=game_days[i],
                value=f'> Home: {home_teams[i]}\n> Away: {away_teams[i]}\n> Time: {game_times[i]}',
                inline=False
            )
        else:
            schedule_embed.add_field(
                name=game_days[i],
                value=f'> Home: {home_teams[i]}\n> Away: {away_teams[i]}\n> Time: {game_times[i]}',
                inline=False
            )

    await schedule_channel.send(embed=schedule_embed)

async def setup(bot):
    print("Adding admin commands to bot")
    bot.add_command(admin)