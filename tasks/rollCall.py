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


def build_gametime_embed(game_datetime: datetime, home_team: str, away_team: str, url: str | None = None) -> discord.Embed:
    """Build a standard gametime embed for roll-call notifications."""
    gametime_embed = discord.Embed(
        color=discord.Color.brand_green(),
        title="Next Game",
        url=url
    )
    gametime_embed.add_field(name="Game Time:", value=game_datetime.strftime("%A %B %d at %I:%M %p"), inline=False)
    gametime_embed.add_field(name="Home Team:", value=home_team, inline=False)
    gametime_embed.add_field(name="Away Team:", value=away_team, inline=False)
    return gametime_embed


async def post_gametime_embed(channel: discord.TextChannel, mention_str: str | None, game_datetime: datetime, home_team: str, away_team: str, url: str | None = None) -> discord.Message:
    """Send a gametime embed to the provided channel with an optional mention."""
    gametime_embed = build_gametime_embed(game_datetime, home_team, away_team, url)
    if mention_str:
        return await channel.send(mention_str, embed=gametime_embed)
    return await channel.send(embed=gametime_embed)


utc = timezone.utc
send_time = time(hour=18, minute=0, tzinfo=utc)


async def setup(bot):
    print("Entering rollcall task setup command")
    rollCall.start(bot)
    # On startup, restore any already-configured upcoming roll-calls
    try:
        await restore_startup_rollcalls(bot)
    except Exception as e:
        print(f"Error restoring startup rollcalls: {e}")


"""
Asynchronous task that checks the team's schedule and posts a roll-call message to the
attendance channel for the next upcoming game within the next six days. This function
is intended to be run (or scheduled) once per day — the current implementation only
performs actions when the current weekday is Tuesday (datetime.today().weekday() == 1).
"""
@tasks.loop(time=send_time)
async def rollCall(bot):
    current_weekday = datetime.today().weekday()

    # change loop to be day == 1 for Tuesday
    if current_weekday == 1:

        # Iterate over each of the guilds in the bot
        for guild in bot.guilds:
            await create_roll_calls(guild)


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
            # store only the datetime in the config (TypedDict expects datetime | None)
            channel_config['next_game'] = next_game_data.datetime

        # Build and send the gametime embed and roll-call view
        await post_gametime_embed(
            channel,
            mention_str,
            next_game_data.datetime,
            next_game_data.home_team,
            next_game_data.away_team,
            schedule_url,
        )
        rollcall_view = RollCallView(next_game_data.datetime)

        # Send the roll call view
        await channel.send(view=rollcall_view)

        # Set up the reminder to disable attendance and remind players two hours before game time
        set_reminder_time = next_game_data.datetime - timedelta(hours=2)
        asyncio.create_task(schedule_reminder(
            set_reminder_time, channel, "The game is starting in 2 hours! Please make sure you're ready to play!"))


async def restore_startup_rollcalls(bot):
    """When the bot starts, post roll-call embeds for channels that already
    have a `next_game` set in the future and restore the attendance embed/view.
    """
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        for channel in get_roll_call_channels(guild):
            channel_config = get_channel_config(guild, channel.name)
            if not channel_config:
                continue

            next_game_dt = channel_config.get('next_game')
            if not next_game_dt:
                continue

            # Only restore for future games
            if not isinstance(next_game_dt, datetime) or next_game_dt <= now:
                continue

            # Try to get fresh game details from the schedule parser
            schedule_url, next_game_data = schedule_parser.get_next_game(guild, channel.name)

            # Build gametime embed (prefer fresh data if available)
            if next_game_data:
                gametime = next_game_data.datetime
                home = next_game_data.home_team
                away = next_game_data.away_team
                url = schedule_url
            else:
                gametime = next_game_dt
                home = "TBD"
                away = "TBD"
                url = None

            # Determine mention string
            try:
                mention_str = await get_role_mention_string(guild, channel, channel_config)
            except Exception:
                mention_str = "@everyone"

            # Send gametime embed
            try:
                await post_gametime_embed(channel, mention_str, gametime, home, away, url)
            except Exception as e:
                print(f"Failed to send gametime embed for {guild.name}/{channel.name}: {e}")
                continue

            # Send current attendance lineup using existing config
            try:
                lineup = lineup_embed(guild, channel.name)
                lineup_msg = await channel.send(embed=lineup)
            except Exception as e:
                print(f"Failed to send lineup embed for {guild.name}/{channel.name}: {e}")
                continue

            # Attach a RollCallView and set its message_id so callbacks edit the lineup
            try:
                rollcall_view = RollCallView(next_game_dt)
                rollcall_view.message_id = lineup_msg.id
                await channel.send(view=rollcall_view)
            except Exception as e:
                print(f"Failed to attach rollcall view for {guild.name}/{channel.name}: {e}")
                # continue anyway

            # Schedule the reminder task
            try:
                set_reminder_time = next_game_dt - timedelta(hours=2)
                asyncio.create_task(schedule_reminder(set_reminder_time, channel, "The game is starting in 2 hours! Please make sure you're ready to play!"))
            except Exception as e:
                print(f"Failed to schedule reminder for {guild.name}/{channel.name}: {e}")


async def get_role_mention_string(guild: discord.Guild, channel: discord.TextChannel, channel_config: ChannelConfig | None) -> str:
    """Returns the roles from config to mention on the roll call notifications, or @everyone if none are found."""
    mention_str = ""
    role_names: list[str] = channel_config.get("role_names", []) if channel_config is not None else []
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
    


async def schedule_reminder(target_time: datetime, channel: discord.TextChannel, message: str):
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
    player_tracking: dict[str, str] = {}
    message_id: int | None = None

    def __init__(self, send_time, timeout=216000):
        super().__init__(timeout=timeout)
        self.player_tracking = {}
        self.message_id = None

    async def on_timeout(self):
        self.player_tracking = {}

    @discord.ui.button(label="In", emoji="✅", style=discord.ButtonStyle.green, custom_id="in-skater")
    async def in_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.channel
        assert guild is not None and channel is not None
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            assert self.message_id is not None
            msg = await channel.fetch_message(self.message_id)
            helper.clear_name(guild, channel.name, user_name)
            self.player_tracking[user_name] = "In"
            await send_line_up(guild, user_name, AttendanceType.SKATERS, channel, msg)
        else:
            if self.message_id is None:
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
        assert guild is not None and channel is not None
        channel_config = get_channel_config(guild, channel.name)
        assert channel_config is not None

        saved_goalie = channel_config['attendance'][AttendanceType.GOALIE.value]
        user_name = interaction.user.display_name
        user_mention = interaction.user.mention

        # Allow the same user to re-click the Goalie button even if they're already set as goalie.
        if saved_goalie == "" or saved_goalie == user_name or saved_goalie == user_mention:
            if user_name in self.player_tracking:
                msg = await channel.fetch_message(self.message_id)
                helper.clear_name(guild, channel.name, user_name)
                self.player_tracking[user_name] = "In - G"
                await send_line_up(guild, user_name, AttendanceType.GOALIE, channel, msg)
            else:
                if self.message_id is None:
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
        assert guild is not None and channel is not None
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            assert self.message_id is not None
            msg = await channel.fetch_message(self.message_id)
            helper.clear_name(guild, channel.name, user_name)
            self.player_tracking[user_name] = "In - Sub"
            await send_line_up(guild, user_name, AttendanceType.SUBS, channel, msg)
        else:
            if self.message_id is None:
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
        assert guild is not None and channel is not None
        user_name = interaction.user.display_name

        if user_name in self.player_tracking:
            assert self.message_id is not None
            msg = await channel.fetch_message(self.message_id)

            helper.clear_name(guild, channel.name, user_name)

            self.player_tracking[user_name] = "Out"
            await send_line_up(guild, user_name, AttendanceType.OUT, channel, msg)
        else:
            if self.message_id is None:
                self.message_id = await send_line_up(guild, user_name, AttendanceType.OUT, channel, None)
            else:
                msg = await channel.fetch_message(self.message_id)
                await send_line_up(guild, user_name, AttendanceType.OUT, channel, msg)
            self.player_tracking[user_name] = "Out"


async def send_line_up(guild: discord.Guild, user_name: str, position: AttendanceType, channel: discord.TextChannel, msg: discord.Message | None) -> int | None:
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
    assert channel_config is not None
    player = helper.get_name_mention(guild, user_name)

    if position.value != AttendanceType.GOALIE.value:
        channel_config['attendance'][position.value].append(player)
    else:
        channel_config['attendance'][AttendanceType.GOALIE.value] = player
    lineup = lineup_embed(guild, channel.name)
    if msg is not None:
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
    assert channel_config is not None
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
