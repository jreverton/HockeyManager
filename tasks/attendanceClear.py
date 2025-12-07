import settings

from datetime import datetime, time, timedelta,timezone
from discord.ext import tasks

utc = timezone.utc
send_time = time(hour=23, minute=0, tzinfo=utc)

async def setup(bot):
    print("Entering attendanceClear task setup command")
    attendanceClear.start(bot)


@tasks.loop(time=send_time)
async def attendanceClear(bot):
    day = datetime.today().weekday()

    if day == 0:  # Monday
        for guild in bot.guilds:
            for channel in settings.SERVER_CONFIG[guild.name]['channels']:
                channel['attendance'] = {
                    "Skaters": [],
                    "Subs": [],
                    "Goalie": "",
                    "Out": []
                }
