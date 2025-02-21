import discord
import helper

from datetime import datetime, time, timedelta,timezone
from discord.ext import tasks
from views import RollCallView

utc = timezone.utc
send_time = time(hour=18, minute=0, tzinfo=utc)

@tasks.loop(time=send_time)
async def rollCall(bot):
    day = datetime.today().weekday()
    current_year = str(datetime.today().year)
    today_date =datetime.today().date()
    four_days_later = datetime.today().date() + timedelta(days=4)

    # change loop to be day == 3 for thursday
    if day == 3:

        # Swap the below code for testing in the devserver
        # team_guild = discord.utils.get(bot.guilds, name='dev server 2')
        team_guild = discord.utils.get(bot.guilds, name='Hakuna Ma Tatas')

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
                rollcall_view = RollCallView(send_time) 
                await attendance_channel.send(embed=gametime_embed)
                await attendance_channel.send(f"{tata.mention} Alright boys, who is in?", view=rollcall_view)
                break
            elif i == len(game_days) - 1:
                bye_week = True
        
        if bye_week:
            await attendance_channel.send(f"{tata.mention} No game this week boys! Have a good weekend!")
            bye_week = False
    

async def setup(bot):
    print("Entering rollcall task setup command")
    rollCall.start(bot)