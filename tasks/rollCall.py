import asyncio
import discord
import helper
from guild import get_roll_call_channels, get_channel_config
from guild.config import get_guild_config
from guild.models import AttendanceType, ChannelConfig
from pprint import pprint
from schedule import parser as schedule_parser

from datetime import datetime, time, timedelta, timezone
from discord.ext import tasks
from discord.ui import View

utc = timezone.utc
send_time = time(hour=18, minute=0, tzinfo=utc)


async def setup(bot):
    print("Entering rollcall task setup command")
    rollCall.start(bot)


"""
Asynchronous task that checks the team's schedule and posts a roll-call message to the
attendance channel for the next upcoming game within the next six days. This function
is intended to be run (or scheduled) once per day — the current implementation only
performs actions when the current weekday is Tuesday (datetime.today().weekday() == 1).
"""
@tasks.loop(time=send_time)
async def rollCall(bot):
    current_weekday = datetime.today().weekday()
    # current_year = str(datetime.today().year)
    # current_date = datetime.today().date()
    # six_days_later = datetime.today().date() + timedelta(days=6)

    # change loop to be day == 1 for Tuesday
    if current_weekday == 1:

        # Iterate over each of the guilds in the bot
        for guild in bot.guilds:
            await create_roll_calls(guild)

        # # Swap the below code for testing in the devserver
        # team_guild = discord.utils.get(bot.guilds, name="exile server")
        # # team_guild = discord.utils.get(bot.guilds, name='Hakuna Ma Tatas')

        # tata =  discord.utils.get(team_guild.roles, name="Tata")
        # attendance_channel = discord.utils.get(team_guild.channels, name="📤-📥-attendance")
        # home_teams, away_teams, game_days, game_times = helper.pull_schedule(team_guild.name)
        # bye_week = False

        # for i in range(len(game_days)):
        #     game_date = datetime.strptime(game_days[i] + " " + current_year, "%a, %b %d %Y").date()
        #     if current_date <= game_date< six_days_later:
        #         gametime_embed = discord.Embed(
        #             color=discord.Color.blue(),
        #             title="Next Game"
        #         )
        #         gametime_embed.add_field(name="Date:", value=game_days[i], inline=False)
        #         gametime_embed.add_field(name="Time:", value=game_times[i], inline=False)
        #         gametime_embed.add_field(name="Home Team:", value=home_teams[i], inline=False)
        #         gametime_embed.add_field(name="Away Team:", value=away_teams[i], inline=False)
        #         rollcall_view = RollCallView(send_time) 
        #         await attendance_channel.send(embed=gametime_embed)
        #         await attendance_channel.send(f"{tata.mention} Alright boys, who is in?", view=rollcall_view)
        #         break
        #     elif i == len(game_days) - 1:
        #         bye_week = True
        
        # if bye_week:
        #     await attendance_channel.send(f"{tata.mention} No game this week boys! Have a good weekend!")
        #     bye_week = False


async def create_roll_calls(guild: discord.Guild):
    """ Iterate over all the roll call channels and send roll-call messages """
    for channel in get_roll_call_channels(guild):
        # Get the channel config to save data
        channel_config = get_channel_config(guild, channel.name)
        mention_str = await get_role_mention_string(guild, channel, channel_config)

        # Check the schedule
        schedule_url, next_game_data = schedule_parser.get_next_game(guild, channel.name)

        # Check if there is a next game
        if not next_game_data:
            await channel.send("No upcoming games found in the schedule.")
            if channel_config is not None:
                channel_config['next_game'] = None
            continue
        
        # Check for a game in the next week
        if next_game_data.datetime > datetime.now(timezone.utc) + timedelta(days=7):
            await channel.send(f"{mention_str} Looks like a bye week. Rest up!")
            if channel_config is not None:
                channel_config['next_game'] = None
            continue
        
        # Save the next game to the channel config
        if channel_config is not None:
            channel_config['next_game'] = next_game_data

        # Build the embeds to send game information and roll-call view
        gametime_embed = discord.Embed(
            color=discord.Color.brand_green(),
            title="Next Game", 
            url=schedule_url
        )
        gametime_embed.add_field(name="Game Time:", value=next_game_data.datetime.strftime("%A %B %d at %I:%M %p"), inline=False)
        gametime_embed.add_field(name="Home Team:", value=next_game_data.home_team, inline=False)
        gametime_embed.add_field(name="Away Team:", value=next_game_data.away_team, inline=False)
        rollcall_view = RollCallView(next_game_data.datetime) 

        # Send the next game message
        await channel.send(mention_str, embed=gametime_embed)

        # Send the roll call view
        await channel.send(view=rollcall_view)

        # Set up the reminder to disable attendance and remind players two hours before game time
        set_reminder_time = next_game_data.datetime - timedelta(hours=2)
        asyncio.create_task(schedule_reminder(
            set_reminder_time, channel, "The game is starting in 2 hours! Please make sure you're ready to play!"))


async def get_role_mention_string(guild: discord.Guild, channel: discord.Channel, channel_config: ChannelConfig) -> str:
    """Returns the roles from config to mention on the roll call notifications, or @everyone if none are found."""
    mention_str = ""
    role_names: list[str] = channel_config.get("role_names", []) if channel_config else []
    if (role_names):
        for role_name in role_names:
            role = discord.utils.get(guild.roles, name=role_name)

            # If role is not found in guild, send a message to the bot channel
            if role is None:
                bot_channel = discord.utils.get(guild.text_channels, id=get_guild_config(guild)["bot_channel"])
                if (bot_channel):
                    await bot_channel.send(f"Role '{role_name}' not found in guild '{guild.name}' for roll-call in {channel.name}.")
                else:
                    await channel.send(f"Role '{role_name}' not found in guild '{guild.name}'.")
            else:
                mention_str = mention_str + f" {role.mention}"
    if mention_str == "":
        mention_str = "@everyone"
    
    return mention_str
    


async def schedule_reminder(target_time: datetime, channel: discord.Channel, message: str):
    """Schedules a one-off reminder message to be sent to a specific channel at a target time."""
    now = datetime.now(timezone.utc)
    delay = (target_time - now).total_seconds()

    # TOOO JRE: Remove developer override to set delay to 10 seconds
    # delay = 10

    if delay > 0:
        await asyncio.sleep(delay)
        await channel.send(message)


class RollCallView(View):
    '''
        This class subclasses the View class in discord. It utilizes buttons to and views to send
        three buttons for accepting roll call
    '''
    # rollcall view properties
    player_tracking = {}
    message_id = ""

    def __init__(self, send_time, timeout=216000):
        super().__init__(timeout=timeout)
        self.player_tracking = {}
        self.message_id = ""

    async def on_timeout(self):
        self.player_tracking = {}

    @discord.ui.button(label="In", emoji="✅", style=discord.ButtonStyle.green, custom_id="in-skater")
    async def in_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.channel
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            msg = await channel.fetch_message(self.message_id)
            helper.clear_name(guild, channel.name, user_name)
            self.player_tracking[user_name] = "In"
            await send_line_up(guild, user_name, AttendanceType.SKATERS, channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await send_line_up(guild, user_name, AttendanceType.SKATERS, channel, None)
            else:
                msg = await channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.SKATERS, channel, msg)
            self.player_tracking[user_name] = "In - Skater"

    @discord.ui.button(label="Goalie", emoji="🥅", style=discord.ButtonStyle.blurple, custom_id="in-goalie")
    async def goalie_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.channel
        channel_config = get_channel_config(guild, channel.name)

        saved_goalie = channel_config['attendance'][AttendanceType.GOALIE]
        if saved_goalie == "" or saved_goalie == interaction.user.display_name:
            user_name = interaction.user.display_name
            if user_name in self.player_tracking:
                msg = await channel.fetch_message(self.message_id)
                helper.clear_name(guild, channel.name, user_name)
                self.player_tracking[user_name] = "In - G"
                await send_line_up(guild, user_name, AttendanceType.GOALIE, channel, msg)
            else:
                if self.message_id == "":
                    self.message_id = await send_line_up(guild, user_name, AttendanceType.GOALIE, channel, None)
                else:
                    msg = await interaction.channel.fetch_message(self.message_id)
                    await send_line_up(guild, user_name, AttendanceType.GOALIE, channel, msg)
            self.player_tracking[user_name] = "In - G"
        else:
            await interaction.channel.send(
                "A Goalie is already selected. He will have to move positions before a new goalie can be selected")

    @discord.ui.button(label="Sub", emoji="👤", style=discord.ButtonStyle.grey, custom_id="in-sub")
    async def sub_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.channel
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            msg = await channel.fetch_message(self.message_id)
            helper.clear_name(guild, channel.name, user_name)
            self.player_tracking[user_name] = "In - Sub"
            await send_line_up(guild, user_name, AttendanceType.SUBS, channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await send_line_up(guild, user_name, AttendanceType.SUBS, channel, None)
            else:
                msg = await channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.SUBS, channel, msg)
            self.player_tracking[user_name] = "In - Sub"

    @discord.ui.button(label="Out", emoji="✖️", style=discord.ButtonStyle.red, custom_id="out")
    async def out_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.channel
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            msg = await channel.fetch_message(self.message_id)

            helper.clear_name(guild, channel.name, user_name)

            self.player_tracking[user_name] = "Out"
            await send_line_up(guild, user_name, AttendanceType.OUT, channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await send_line_up(guild, user_name, AttendanceType.OUT, channel, None)
            else:
                msg = await channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.OUT, channel, msg)
            self.player_tracking[user_name] = "Out"


async def send_line_up(guild: discord.Guild, user_name: str, position: AttendanceType, channel: discord.Channel, msg: str):
    """
        This function sends or updates the lineup embed in the attendance channel
        Parameters:
            guild - the guild/server
            user - string name of the user
            position - enum position of the player (Skater, Goalie, Sub, Out)
            channel - discord channel object to send the message to
            msg - discord message object to edit if updating an existing message
        Returns:
            message id if a new message is sent, None if editing an existing message
    """
    print(f"send_line_up({guild.name}, {user_name}, {position.value}, {channel}, {msg})")

    channel_config = get_channel_config(guild, channel.name)
    player = helper.get_name_mention(guild, user_name)

    if position.value != AttendanceType.GOALIE.value:
        channel_config['attendance'][position.value].append(player)
    else:
        channel_config['attendance'][AttendanceType.GOALIE.value] = player
    lineup = lineup_embed(guild, channel.name)
    if msg:
        await msg.edit(embed=lineup)
    else:
        msg = await channel.send(embed=lineup)
        return msg.id
    

def lineup_embed(guild: discord.Guild, channel_name):
    lineup_embed = discord.Embed(
        color=discord.Color.blue(),
        title="Current Line Up"
    )

    skater_lineup = ""
    subs_lineup = ""
    out_lineup = ""

    channel_config = get_channel_config(guild, channel_name)
    attendance_array = channel_config['attendance']

    # Populate the lineup strings
    skater_list: list = attendance_array[AttendanceType.SKATERS.value]
    for value in skater_list:
        skater_lineup = skater_lineup + f"> {value}\n"
    
    sub_list: list = attendance_array[AttendanceType.SUBS.value]
    for value in sub_list:
        subs_lineup = subs_lineup + f"> {value}\n"

    if attendance_array[AttendanceType.GOALIE.value] == "":
        goalie_name = ""
    else:
        goalie_name = f"> {attendance_array[AttendanceType.GOALIE.value]}"

    out_list: list = attendance_array[AttendanceType.OUT.value]
    for value in out_list:
        out_lineup = out_lineup + f"> {value}\n"

    # Build out the embed with attendence info
    lineup_embed.add_field(
        name=f"✅ In ({len(skater_list)}):",
        value=skater_lineup,
        inline=True
    )
    lineup_embed.add_field(
        name=f"❌ Out ({len(out_list)}):",
        value=out_lineup,
        inline=True
    )
    lineup_embed.add_field(
        name="🥅 Goalie:",
        value=goalie_name,
        inline=False
    )
    lineup_embed.add_field(
        name=f"👤 Available Subs ({len(sub_list)}):",
        value=subs_lineup,
        inline=True
    )

    return lineup_embed
