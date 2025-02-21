import discord
import helper
import settings

from discord.ext import commands
from views import WhoAreYouView


def run():
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
    hakuna_manager = commands.Bot(command_prefix="!", intents=intents)

    @hakuna_manager.event    
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

    @hakuna_manager.event
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

        # create the empty data dcitionary and pass it to builder function
        settings.SERVER_CONFIG[guild.name] = {}
        helper.create_server_config(settings.SERVER_CONFIG[guild.name], guild.name, guild.id)

        # check to see if the bot and feedback channels exist
        if discord.utils.get(guild.channels, name="bot-commands") != None:
            settings.SERVER_CONFIG[guild.name]['bot_channel'] = discord.utils.get(guild.channels, name="bot-commands").id

        # create the channels
        if settings.SERVER_CONFIG[guild.name]["bot_channel"] == 0:
            # create the private permissions
            overwrites = helper.create_permissons(guild.owner, discord.utils.get(guild.roles, name="Admin"), guild.default_role)
            
            bot = await helper.create_bot_channels(guild, overwrites)

            # update the data dict fort bot id's
            settings.SERVER_CONFIG[guild.name]["bot_channel"] = bot

    @hakuna_manager.event
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

    @hakuna_manager.event
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
        print("Hakuna Ma Tatas are playing.")

        # Load the task files
        for task_file in settings.TASKS_DIR.glob("*.py"):
            if task_file.name != "__init__.py":
                print(f"loading file: {task_file.name}")
                await hakuna_manager.load_extension(f"tasks.{task_file.name[:-3]}")

        # Load commands files
        for command_file in settings.CMDS_DIR.glob("*.py"):
            if command_file.name != "__init__.py":
                print(f"loading file: {command_file.name}")
                await hakuna_manager.load_extension(f"cmds.{command_file.name[:-3]}")

    hakuna_manager.run(settings.DISCORD_API_SECRET)

if __name__ == "__main__":
    run()