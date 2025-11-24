import discord
import helper
import settings
from settings import AttendanceType
from pprint import pprint

from datetime import datetime, time, timedelta, timezone
from discord.ext import tasks
from discord.ui import View

utc = timezone.utc
send_time = time(hour=18, minute=0, tzinfo=utc)

"""
Asynchronous task that checks the team's schedule and posts a roll-call message to the
attendance channel for the next upcoming game within the next four days. This function
is intended to be run (or scheduled) once per day — the current implementation only
performs actions when the current weekday is Thursday (datetime.today().weekday() == 3).
Behavior
- Determines today's date and a cutoff date four days in the future.
- Retrieves the configured guild, the "Tata" role, and the attendance channel from the
    bot's connected guilds.
- Calls helper.pull_schedule(team_guild.name) and expects a tuple of four lists:
    (home_teams, away_teams, game_days, game_times).
    - game_days entries are expected to be formatted like "%a, %b %d" (e.g. "Thu, Nov 03")
        without the year; the current year is appended before parsing.
- Iterates the schedule and finds the first game_date where today_date <= game_date < four_days_later.
    - If a matching game is found:
        - Builds a discord.Embed titled "Next Game" containing Date, Time, Home Team, and Away Team.
        - Instantiates a RollCallView (currently using an external send_time value).
        - Sends the embed to the attendance channel and posts a follow-up message tagging the Tata
            role with the roll-call prompt and the interactive view.
    - If no upcoming game is found in the range, sends a "No game this week" message tagging Tata.
Parameters
- bot: discord.Client | commands.Bot | discord.Bot
        The bot instance used to access connected guilds, roles, and channels.
Returns
- None
Side effects
- Sends one or two messages to the attendance channel in the target guild.
- Relies on global/outer-scope definitions: RollCallView and send_time (must be defined
    in the module or otherwise available in scope).
- May raise exceptions if:
    - The target guild, role, or channel cannot be found.
    - helper.pull_schedule returns unexpected types/lengths.
    - date parsing fails due to unexpected game_days formats.
    - Discord API calls fail (network/permission issues).
Notes and recommendations
- Consider making the target guild name, attendance channel name, role name, and the
    threshold days configurable rather than hard-coded for easier testing and reuse.
- Consider passing send_time (and RollCallView) as parameters or ensuring they are
    explicitly defined to avoid NameError at runtime.
- Add error handling/logging around guild/role/channel lookups, helper.pull_schedule,
    and message sends to make the function more robust and easier to debug.
"""
@tasks.loop(time=send_time)
async def rollCall(bot):
    day = datetime.today().weekday()
    current_year = str(datetime.today().year)
    today_date =datetime.today().date()
    four_days_later = datetime.today().date() + timedelta(days=4)

    # change loop to be day == 3 for thursday
    if day == 3:

        # Swap the below code for testing in the devserver
        team_guild = discord.utils.get(bot.guilds, name="Exile's Test Server")
        # team_guild = discord.utils.get(bot.guilds, name='Hakuna Ma Tatas')

        tata =  discord.utils.get(team_guild.roles, name="Tata")
        attendance_channel = discord.utils.get(team_guild.channels, name="📤-📥-attendance")
        home_teams, away_teams, game_days, game_times = helper.pull_schedule(team_guild.name)
        bye_week = False

        for i in range(len(game_days)):
            game_date = datetime.strptime(game_days[i] + " " + current_year, "%a, %b %d %Y").date()
            if today_date <= game_date< four_days_later:
                gametime_embed = discord.Embed(
                    color=discord.Color.blue(),
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
        guild = interaction.guild.name
        user_name = interaction.user.display_name

        print('in_button_callback()')
        #pprint(interaction.user)
        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)
            helper.clear_name(guild, user_name)
            self.player_tracking[user_name] = "In"
            await send_line_up(guild, user_name, AttendanceType.SKATERS, interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await send_line_up(guild, user_name, AttendanceType.SKATERS, interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.SKATERS, interaction.channel, msg)
            self.player_tracking[user_name] = "In - Skater"

    @discord.ui.button(label="Goalie", emoji="🥅", style=discord.ButtonStyle.blurple, custom_id="in-goalie")
    async def goalie_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name
        saved_goalie = settings.SERVER_CONFIG[guild]['attendance'][AttendanceType.GOALIE]
        if saved_goalie == "" or saved_goalie == interaction.user.display_name:
            user_name = interaction.user.display_name
            if user_name in self.player_tracking:
                msg = await interaction.channel.fetch_message(self.message_id)
                helper.clear_name(guild, user_name)
                self.player_tracking[user_name] = "In - G"
                await send_line_up(guild, user_name, AttendanceType.GOALIE, interaction.channel, msg)
            else:
                if self.message_id == "":
                    self.message_id = await send_line_up(guild, user_name, AttendanceType.GOALIE, interaction.channel, None)
                else:
                    msg = await interaction.channel.fetch_message(self.message_id)
                    await send_line_up(guild, user_name, AttendanceType.GOALIE, interaction.channel, msg)
            self.player_tracking[user_name] = "In - G"
        else:
            await interaction.channel.send(
                "A Goalie is already selected. He will have to move positions before a new goalie can be selected")

    @discord.ui.button(label="Sub", emoji="👤", style=discord.ButtonStyle.grey, custom_id="in-sub")
    async def sub_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)
            helper.clear_name(guild,user_name)
            self.player_tracking[user_name] = "In - Sub"
            await send_line_up(guild, user_name, AttendanceType.SUBS, interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await send_line_up(guild, user_name, AttendanceType.SUBS, interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.SUBS, interaction.channel, msg)
            self.player_tracking[user_name] = "In - Sub"

    @discord.ui.button(label="Out", emoji="✖️", style=discord.ButtonStyle.red, custom_id="out")
    async def out_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)

            helper.clear_name(guild,user_name)

            self.player_tracking[user_name] = "Out"
            await send_line_up(guild, user_name, AttendanceType.OUT, interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await send_line_up(guild, user_name, AttendanceType.OUT, interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.OUT, interaction.channel, msg)
            self.player_tracking[user_name] = "Out"


async def send_line_up(guild_name, user, position: AttendanceType, channel, msg):
    """
        This function sends or updates the lineup embed in the attendance channel
        Parameters:
            guild_name - string name of the guild/server
            user - string name of the user
            position - enum position of the player (Skater, Goalie, Sub, Out)
            channel - discord channel object to send the message to
            msg - discord message object to edit if updating an existing message
        Returns:
            message id if a new message is sent, None if editing an existing message
    """
    print(f"send_line_up({guild_name}, {user}, {position.value}, {channel}, {msg})")
    pprint(settings.SERVER_CONFIG)

    if position.value != AttendanceType.GOALIE.value:
        settings.SERVER_CONFIG[guild_name]['attendance'][position.value].append(user)
    else:
        settings.SERVER_CONFIG[guild_name]['attendance'][AttendanceType.GOALIE.value] = user
    lineup = lineup_embed(guild_name)
    if msg:
        await msg.edit(embed=lineup)
    else:
        msg = await channel.send(embed=lineup)
        return msg.id
    

def lineup_embed(guild_name):
    lineup_embed = discord.Embed(
        color=discord.Color.blue(),
        title="Current Line Up"
    )

    skater_lineup = ""
    subs_lineup = ""
    out_lineup = ""

    attendance_array = settings.SERVER_CONFIG[guild_name]['attendance']

    if attendance_array[AttendanceType.GOALIE.value] == "":
        goalie_name = ""
    else:
        goalie_name = f"> {attendance_array[AttendanceType.GOALIE.value]}"

    skater_list: list = attendance_array[AttendanceType.SKATERS.value]
    for value in skater_list:
        skater_lineup = skater_lineup + f"> {value}\n"
    
    sub_list: list = attendance_array[AttendanceType.SUBS.value]
    for value in sub_list:
        subs_lineup = subs_lineup + f"> {value}\n"

    out_list: list = attendance_array[AttendanceType.OUT.value]
    for value in out_list:
        out_lineup = out_lineup + f"> {value}\n"

    # Build out the embed with attendence info
    lineup_embed.add_field(
        name=f"✅ In ({len(skater_list)}): ",
        value=skater_lineup,
        inline=True
    )
    lineup_embed.add_field(
        name=f"❌ Out ({len(out_list)}): ",
        value=out_lineup,
        inline=True
    )
    lineup_embed.add_field(
        name="🥅 Goalie: ",
        value=goalie_name,
        inline=True
    )
    lineup_embed.add_field(
        name=f"👤 Available Subs ({len(sub_list)}): ",
        value=subs_lineup,
        inline=True
    )

    return lineup_embed
