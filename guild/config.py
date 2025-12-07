"""Guild configuration management functions."""

from pprint import pprint
import discord
import settings
from guild.models import AttendanceType, ServerConfigDict
from guild.models import GuildConfig, ChannelConfig


def create_new_guild_config(server_config: ServerConfigDict, guild: discord.Guild) -> GuildConfig:
    """Create and populate a new guild configuration."""
    guild_config: GuildConfig = GuildConfig(
        id = guild.id,
        bot_channel = 0,
        file_prefix = guild.name.replace(" ", ""),
        roll_call_channel_suffix = "-roll-call",
        season_id = "0",
        channels = []
    )
    
    # Find all roll-call channels and add to the config
    for channel in get_roll_call_channels(guild):
        channel_config: ChannelConfig = ChannelConfig(
            name = channel.name,
            channel_id = channel.id,
            team_id = "0",
            division_id = "0",
            role_names = [],
            next_game = None,
            attendance = {
                AttendanceType.SKATERS.value: [],
                AttendanceType.SUBS.value: [],
                AttendanceType.GOALIE.value: "",
                AttendanceType.OUT.value: []
            }
        )
        guild_config['channels'].append(channel_config)
    
    # Save the new guild config to the server
    server_config[guild.name] = guild_config

    return guild_config


def get_guild_config(guild: discord.Guild) -> GuildConfig:
    """Retrieve guild configuration, creating one if it doesn't exist."""
    saved_settings = settings.SERVER_CONFIG.get(guild.name) or create_new_guild_config(settings.SERVER_CONFIG, guild)

    return saved_settings


def get_channel_config(guild: discord.Guild, channel_name: str) -> ChannelConfig | None:
    """Retrieve a channel configuration by name (case-insensitive)."""
    # Find the first channel dict whose 'name' property equals channel_name
    guild_data = get_guild_config(guild)
    channel_list = guild_data.get('channels', [])
    channel_data = next((ch for ch in channel_list if str(ch.get('name', '')).lower() == str(channel_name).lower()), None)
    if channel_data is None:
        print(f"Channel config not found for channel: {channel_name}")
        return None
    
    return channel_data


def get_roll_call_channels(guild: discord.Guild) -> list[discord.TextChannel]:
    """Get all text channels in the guild that match the roll-call suffix."""
    guild_config: GuildConfig = get_guild_config(guild)
    channel_suffix = guild_config.get("roll_call_channel_suffix", "-roll-call")
    return [
        c for c in guild.channels
        if isinstance(c, discord.TextChannel) and c.name.lower().endswith(channel_suffix)
    ]
