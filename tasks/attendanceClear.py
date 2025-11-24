import settings

from datetime import datetime, time, timedelta,timezone
from discord.ext import tasks

utc = timezone.utc
send_time = time(hour=23, minute=0, tzinfo=utc)

@tasks.loop(time=send_time)
async def attendanceClear(bot):
    day = datetime.today().weekday()

    if day == 6:
        for guild in bot.guilds:
            settings.SERVER_CONFIG[guild.name]['attendance'] = {
                "Skaters": [],
                "Subs": [],
                "Goalie": "",
                "Out": []
            } 
    
async def setup(bot):
    print("Entering attendanceClear task setup command")
    attendanceClear.start(bot)