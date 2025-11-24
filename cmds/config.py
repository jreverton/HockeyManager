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

@config.command(brief="change the file name prefix")
@commands.check(helper.is_admin)
async def changeFilePrefix(ctx, prefix: str):
    '''
        Command: changeFilePrefix
        desc:
            change the file prerfix attached to each server file. This will 
            affect sending the attendance, archiving channels, and saving
            the server configfuration. It will deelte the old file so as 
            not to clutter the server
        parameter:
            ctx - standard context object for a command, 
                see https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
            prefix - string file name
    '''
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
    await bot_channel.send("File Prefix Changed")
    

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
    bot_channel = await helper.get_bot_channel(ctx)
    
    # check if server data is laoded
    if settings.SERVER_CONFIG:
        # create the embed
        config_embed = discord.Embed(
            title="Current Configuration",
            description="Here is your current configuration:",
            color=discord.Color.dark_purple()
        )

        # loop through the config
        for key in settings.SERVER_CONFIG[ctx.guild.name]:
            config_embed.add_field(name=key, value=settings.SERVER_CONFIG[ctx.guild.name][key], inline=False)

        await bot_channel.send(embed=config_embed)
    else:
        await bot_channel.send("No config file loaded.")

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
    # collect the file name
    file_name = settings.DATA_DIR / (ctx.guild.name.replace(" ", "") + '_config.json')

    # use helper function to load config so same logic can be reused elsewhere
    helper.load_server_config(file_name, settings.SERVER_CONFIG, ctx.bot)

    # let the admin know
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send("Config Loaded")

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
    helper.save_config(ctx)

    # let the admin know
    bot_channel = await helper.get_bot_channel(ctx)
    await bot_channel.send("Configuration has been saved")

async def setup(bot):
    print("Adding config commands to bot")
    bot.add_command(config)