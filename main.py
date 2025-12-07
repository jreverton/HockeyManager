from datetime import datetime
import discord
from cmds.config import load_server_config
from guild.config import create_new_guild_config
from guild.models import GuildConfig
import helper
import settings
import schedule.parser as parser
  
from tasks.rollCall import create_roll_calls
from views import WhoAreYouView
from pprint import pprint
from discord.ext import commands

def run(): # James version
    '''
        Function: Run
        Desc:
            main application of the bot. Starts the processes and setup
            for the bot to porperly run.
        Parameters:
            None
    '''
    # Intent seup, necessary with new bot api
    intents = discord.Intents.default()
    intents.guilds = True           # Required for guild-related events
    intents.members = True          # Required to access guild members
    intents.messages = True         # Required to receive messages in guilds and DMs
    intents.message_content = True  # Required to access message.content, message.embeds, etc.

    # Create the bot name and instance with the desired command prefix 
    # and necessary intents
    edm_manager = commands.Bot(command_prefix="!", intents=intents)

    # TODO JRE: Remove this temporary rollcall command
    @edm_manager.command(name="rollcall")
    async def roll_call(ctx: commands.Context):
        if ctx.guild is not None:
            await create_roll_calls(ctx.guild)
        else:
            await ctx.send("This command can only be used in a server (guild).")

    @edm_manager.event
    async def on_ready():
        '''
            Event Override: on_ready
            Desc:
                when the bot boots up when it is ready to run the bot collect
                the necessary files from the tasks and commands directories.
                It will then load them into the bot
            Parameters:
                None
        '''
        print("EDM Manager is loading...")

        # Load the task files
        for task_file in settings.TASKS_DIR.glob("*.py"):
            if task_file.name != "__init__.py":
                print(f"loading file: {task_file.name}")
                await edm_manager.load_extension(f"tasks.{task_file.name[:-3]}")

        # Load commands files
        for command_file in settings.CMDS_DIR.glob("*.py"):
            if command_file.name != "__init__.py":
                print(f"loading file: {command_file.name}")
                await edm_manager.load_extension(f"cmds.{command_file.name[:-3]}")

        # TODO JRE: Remove this temporary config load
        # Load any server configurations from file
        for config in settings.DATA_DIR.glob("*_config_new.json"):
        # for config in settings.DATA_DIR.glob("*_config.json"):
            print(f"Loading server config file: {config.name}")
            load_server_config(config, settings.SERVER_CONFIG, edm_manager)

    
    @edm_manager.event
    async def on_guild_join(guild: discord.Guild):
        '''
            Event Override: on_guild_join
            desc:
                this will override the on guild join for the bot and will 
                display a hello message in the system channel. This way 
                some of the house keeping is told to the server admins/mods
            parameter:
                guild - Standard guild object. See
                    https://discordpy.readthedocs.io/en/stable/api.html#guild
        '''

        print('on_guild_join()')
        pprint(guild)

        # create a new guild_config and pass it to builder function
        guild_config: GuildConfig = create_new_guild_config(settings.SERVER_CONFIG, guild)

        # check to see if the bot channel exists
        if discord.utils.get(guild.channels, name="manager-bot") != None:
            bot_channel: discord.TextChannel | None = discord.utils.get(guild.text_channels, name="manager-bot")
            guild_config["bot_channel"] = bot_channel.id if bot_channel else 0

        # create the channels
        if guild_config["bot_channel"] == 0:
            # create the private permissions
            overwrites = helper.create_permissons(guild.owner, discord.utils.get(guild.roles, name="Admin"), guild.default_role)
            
            bot_channel_id = await helper.create_bot_channels(guild, overwrites)

            # update the data dict for bot id's
            guild_config["bot_channel"] = bot_channel_id

    edm_manager.run(settings.DISCORD_API_SECRET) # type: ignore








''' Zach's original run code '''
def orig_run(): # Zach version
    '''
        Function: Run
        Desc:
            main application of the bot. Starts the processes and setup
            for the bot to porperly run.
        Parameters:
            None
    '''
    # Intent  seup, necessary with new bot api
    intents = discord.Intents.all()

    # create the bot name and instance with the desired command prefix 
    # and necessary intents
    edm_manager = commands.Bot(command_prefix="!", intents=intents)

    @edm_manager.event    
    async def on_command_error(ctx, error):
        '''
            Event Override: on_command_error
            Desc:
                custom response to a permissions check failure
            Parameter:
                ctx - context error provided by the command system
                error - the error that was thrown
        '''
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You dont have permissions to use this command.")

    @edm_manager.event
    async def on_guild_join(guild):
        '''
            Event Override: on_guild_join
            desc:
                this will override the on guild join for the bot and will 
                display a hello message in the system channel. This way 
                some of the house keeping is told to the server admins/mods
            parameter:
                guild - Standard guild object. See
                    https://discordpy.readthedocs.io/en/stable/api.html#guild
        '''

        print('on_guild_join()')
        pprint(guild)

        # create the empty data dictionary and pass it to builder function
        settings.SERVER_CONFIG[guild.name] = {}
        helper.create_new_guild_config(settings.SERVER_CONFIG[guild.name], guild.name, guild.id)

        # check to see if the bot and feedback channels exist
        if discord.utils.get(guild.channels, name="manager-bot") != None:
            settings.SERVER_CONFIG[guild.name]['bot_channel'] = discord.utils.get(guild.channels, name="manager-bot").id

        # create the channels
        if settings.SERVER_CONFIG[guild.name]["bot_channel"] == 0:
            # create the private permissions
            overwrites = helper.create_permissons(guild.owner, discord.utils.get(guild.roles, name="Admin"), guild.default_role)
            
            bot = await helper.create_bot_channels(guild, overwrites)

            # update the data dict fort bot id's
            settings.SERVER_CONFIG[guild.name]["bot_channel"] = bot

    @edm_manager.event
    async def on_member_join(member):
        '''
            Event Override: on_member_join
            Desc:
                create a new message to the user to select the correct roles.
                This allows the user to see or not see certain channels and
                categories
            Parameter:
                Member - user who has just the joined the server, supplied by the event
        '''
        member_choice = WhoAreYouView()
        await member.guild.system_channel.send(f"Hello {member.name}, welcome to the {member.guild.name}. Please choose one of the following:", view=member_choice)

    @edm_manager.event
    async def on_ready():
        '''
            Event Override: on_ready
            Desc:
                when the bot boots up when it is ready to run the bot collect
                the necessary files from the tasks and commands directories.
                It will then load them into the bot
            Parameters:
                None
        '''
        print("EDM is playing.")

        # Load the task files
        for task_file in settings.TASKS_DIR.glob("*.py"):
            if task_file.name != "__init__.py":
                print(f"loading file: {task_file.name}")
                await edm_manager.load_extension(f"tasks.{task_file.name[:-3]}")

        # Load commands files
        for command_file in settings.CMDS_DIR.glob("*.py"):
            if command_file.name != "__init__.py":
                print(f"loading file: {command_file.name}")
                await edm_manager.load_extension(f"cmds.{command_file.name[:-3]}")

    edm_manager.run(settings.DISCORD_API_SECRET)

if __name__ == "__main__":
    run()