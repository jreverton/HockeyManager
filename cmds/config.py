import discord
import helper
import json
import os
import settings

from discord.ext import commands

@commands.group(brief="Server Configuration Controls")
async def config(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("A subcommand was not passed")

'''
"!config changeFilePrefix <newPrefix>" command
'''
@config.command(brief="change the file name prefix")
@commands.check(helper.is_admin)
async def changeFilePrefix(ctx: commands.Context, prefix: str):
    '''
        Command: changeFilePrefix
        desc:
            change the file prefix attached to each server file. This will 
            affect sending the attendance, archiving channels, and saving
            the server configuration. It will delete the old file so as 
            not to clutter the server
        parameter:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
            prefix - string file name
    '''
    assert ctx.guild is not None
    # collects the old prefix
    old_prefix = settings.SERVER_CONFIG[ctx.guild.name]['file_prefix']

    # delete files with the old prefix
    for fi in os.listdir("data"):
        if old_prefix in fi:
            os.remove(settings.DATA_DIR / fi)
    # set the new prefix in the config
    settings.SERVER_CONFIG[ctx.guild.name]['file_prefix'] = prefix

    await save(ctx)

    # let the admin know
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send(f"File Prefix Changed from {old_prefix} to {prefix}")
    

'''
"!config list" command
'''
@config.command(brief="list the current configuration")
@commands.check(helper.is_admin)
async def list(ctx):
    '''
        Command: listConfig
        desc:
            creates an embed detailing the server's current configuration. 
            This can be changed using the appropriate commands
        parameters:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
    '''
    assert ctx.guild is not None
    bot_channel = await helper.get_bot_channel(ctx)
    
    # check if server data is laoded
    if settings.SERVER_CONFIG:
        # create the embed
        config_embed = discord.Embed(
            title="Current Configuration",
            color=discord.Color.dark_purple()
        )

        # loop through the config
        for key in settings.SERVER_CONFIG[ctx.guild.name]:
            config_embed.add_field(name=key, value=settings.SERVER_CONFIG[ctx.guild.name][key], inline=False)

        await bot_channel.send(embed=config_embed)
    else:
        await bot_channel.send("No config file loaded.")

'''
"!config load" command
'''
@config.command(brief="load the server configuration from a file")
@commands.check(helper.is_admin)
async def load(ctx):
    '''
        Command: loadConfig
        desc:
            This command allows the user to load the config settings for their
            specific server. This allows them to load any saved configuration
            such as changes to the class dictionary and then target message
        Paramters:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html    
    '''
    assert ctx.guild is not None
    # collect the file name
    file_name = settings.DATA_DIR / (ctx.guild.name.replace(" ", "") + '_config.json')

    # load the config from file
    load_server_config(file_name, settings.SERVER_CONFIG, ctx.bot)

    # let the admin know
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send("Config Loaded")

'''
"!config save" command
'''
@config.command(brief="save the current configuration to a file")
@commands.check(helper.is_admin)
async def save(ctx):
    '''
        Command: save
        desc:
            This command allows the user to save the current config settings 
            for their specific server. Keeping data persistance in the event
            of a bot reboot. The load command will need to be called.
        Paramters:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html 
    '''
    try:
        save_config(ctx)
    except Exception as e:
        bot_channel = await helper.get_bot_channel(ctx)
        await bot_channel.send(f"Error saving configuration: {e}")
        return

    # let the admin know
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send("Configuration has been saved")


"""
load_server_config: Helper function to load a server config file
"""
def load_server_config(file_path, server_config, bot=None):
    """
    Load a server config JSON file into the provided `server_config` dict.

    Parameters:
    - file_path: pathlib.Path or string pointing to a `_config.json` file
    - server_config: dict to update (e.g., `settings.SERVER_CONFIG`)
    - bot: optional discord.Bot instance. If provided, the function will
      try to map the saved `id` field to an actual guild and use the
      guild's real name as the key in `server_config`.

    Returns: the key used to store the config in `server_config`.
    """
    # accept either Path or string
    from pathlib import Path
    p = Path(file_path)

    try:
        with open(p, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Failed to load config file {p}: {e}")
        return None
    except FileNotFoundError:
        print(f"Config file not found: {p}")
        return None

    # Prefer to use the guild id stored in the config to locate the guild
    guild_key = None
    try:
        cfg_id = int(cfg.get('id', 0))
    except Exception:
        cfg_id = 0

    if bot and cfg_id:
        guild = bot.get_guild(cfg_id)
        if guild:
            guild_key = guild.name

    # Fallback: derive prefix from filename and try to match a guild by prefix
    if not guild_key and bot:
        prefix = p.stem.replace('_config', '')
        for g in bot.guilds:
            if g.name.replace(' ', '') == prefix:
                guild_key = g.name
                break

    # Last resort: use the prefix itself as the key
    if not guild_key:
        guild_key = p.stem.replace('_config', '')

    server_config[guild_key] = cfg
    return guild_key

"""
save_config: Helper function to save a server config to a file
"""
def save_config(ctx):
    # create the file name and ensure data directory exists
    from pathlib import Path
    from datetime import datetime, date

    assert ctx.guild is not None
    data_dir = settings.DATA_DIR if isinstance(settings.DATA_DIR, Path) else Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)

    file_name = data_dir / (settings.SERVER_CONFIG[ctx.guild.name]['file_prefix'] + '_config.json')
    temp_file = file_name.with_suffix(file_name.suffix + '.tmp')

    # custom JSON serializer: convert datetimes to ISO, fallback to string
    def _json_default(o):
        try:
            # datetime, date, and similar objects
            if hasattr(o, 'isoformat'):
                return o.isoformat()
        except Exception:
            pass
        return str(o)

    # save to a temporary file first, then atomically replace the config file
    with open(temp_file, 'w', encoding='utf-8') as cur_config:
        json.dump(settings.SERVER_CONFIG[ctx.guild.name], cur_config, indent=2, ensure_ascii=False, default=_json_default)

    os.replace(temp_file, file_name)


async def setup(bot):
    print("Adding config commands to bot")
    bot.add_command(config)