import discord
import helper
import settings
import schedule.parser as parser

from discord.ext import commands
from tasks.rollCall import RollCallView
from views import WhoAreYouView
from pprint import pprint

def run():
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
    intents.guilds = True         # Required for guild-related events
    intents.messages = True       # Required to receive messages in guilds and DMs
    intents.message_content = True # Required to access message.content, message.embeds, etc.

    # Create the bot name and instance with the desired command prefix 
    # and necessary intents
    edm_manager = commands.Bot(command_prefix="!", intents=intents)

    @edm_manager.command(name="helloworld")
    async def helloworld(ctx: commands.Context):
        """ Respond with hello user """
        print(f"Hello World: {ctx.author.mention}")
        pprint(ctx.channel)
        await ctx.send(f"Hello {ctx.author.mention}!")

    @edm_manager.command(name="schedule")
    async def grab_shedule(ctx):
        """ Call Johnson's schedule parser and return schedule """
        team_name, next_game_data = parser.james()

        # TODO: Format the output nicely for Discord message

        print(f"Schedule for {team_name}:")
        pprint(next_game_data)
        # await ctx.send(f"{team_name}\n\n {next_game}")
        await ctx.send(f"/create title:'{next_game_data.home_team} vs {next_game_data.away_team}' datetime:'{next_game_data.datetime}'")
    
    @edm_manager.command(name="load")
    async def load_config(ctx: commands.Context):
        config.load(ctx);
    
    @edm_manager.command(name="rollcall")
    async def create_roll_call(ctx: commands.Context):

        """ Manually trigger a roll call message """
        team_name, next_game_data = parser.james()

        if not next_game_data:
            await ctx.send("No upcoming games found in the schedule.")
            return

        # TODO: Figure out the devserver configuration so we can list players In, Out, Goalie and Sub

        gametime_embed = discord.Embed(
                    color=discord.Color.brand_green(),
                    title="Next Game"
                )
        gametime_embed.add_field(name="Date:", value=next_game_data.datetime.date(), inline=False)
        gametime_embed.add_field(name="Time:", value=next_game_data.datetime.time(), inline=False)
        gametime_embed.add_field(name="Home Team:", value=next_game_data.home_team, inline=False)
        gametime_embed.add_field(name="Away Team:", value=next_game_data.away_team, inline=False)
        rollcall_view = RollCallView(next_game_data.datetime) 
        await ctx.channel.send(embed=gametime_embed)
        await ctx.channel.send(f"Alright, who is in?", view=rollcall_view)


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

        # Load any server configurations from file
        for config in settings.DATA_DIR.glob("*_config.json"):
            print(f"Loading server config file: {config.name}")
            helper.load_server_config(config, settings.SERVER_CONFIG, edm_manager)

    
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

    print("Starting EDM Manager Bot with secret: " + settings.DISCORD_API_SECRET)
    edm_manager.run(settings.DISCORD_API_SECRET)

''' Zach's original run code '''
def orig_run():
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