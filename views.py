import discord
import helper
import settings

from discord.ui import View

class WhoAreYouView(View):

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="I'm a Player", style=discord.ButtonStyle.green, custom_id="player")
    async def player_callback(self, interaction, button):
        await interaction.response.defer()
        role  = discord.utils.get(interaction.guild.roles, name="Tata")

        await interaction.user.add_roles(role)

        await interaction.edit_original_response(content=f"{interaction.user.name}, welcome to the Team!", view=None)

    @discord.ui.button(label="I'm a Fan", style=discord.ButtonStyle.blurple, custom_id="guest")
    async def guest_callback(self, interaction, button):
        await interaction.response.defer()
        role  = discord.utils.get(interaction.guild.roles, name="Fan")

        await interaction.user.add_roles(role)

        await interaction.edit_original_response(content=f"{interaction.user.name}, welcome to the server! Feel free to ping team members to chat or follow the schedule to see our performance for the season.", view=None)

    @discord.ui.button(label="I'm nobody", style=discord.ButtonStyle.grey, custom_id="nobody")
    async def nobody_callback(self, interaction, button):
        await interaction.response.edit_message(content=f"{interaction.user.name}, sorry but non-members are not able to contribute. Pleae contact the team captain or the server owner for assistance", view=None)

class RollCallView(View):
    '''
        This class subclasses the View class in discord. It utilizes buttons to and views to send
        three buttons for accerpting role call
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

    @discord.ui.button(label="Forward", style=discord.ButtonStyle.green, custom_id="in-forward")
    async def forward_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name

        user_name = interaction.user.display_name
        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)
            helper.clear_name(guild,user_name)
            self.player_tracking[user_name] = "In - F"
            await helper.send_line_up(guild, user_name, 'Forwards', interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await helper.send_line_up(guild, user_name, 'Forwards', interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await helper.send_line_up(guild, user_name, 'Forwards', interaction.channel, msg)
            self.player_tracking[user_name] = "In - F"
    
    @discord.ui.button(label="Defense", style=discord.ButtonStyle.green, custom_id="in-defense")
    async def defense_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name

        user_name = interaction.user.display_name
        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)
            helper.clear_name(guild,user_name)
            self.player_tracking[user_name] = "In - D"
            await helper.send_line_up(guild, user_name, 'Defense', interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await helper.send_line_up(guild, user_name, 'Defense', interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await helper.send_line_up(guild, user_name, 'Defense', interaction.channel, msg)
            self.player_tracking[user_name] = "In - D"

    @discord.ui.button(label="Goalie", style=discord.ButtonStyle.blurple, custom_id="in-goalie")
    async def goalie_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name

        if settings.SERVER_CONFIG[guild]['attendance']['Goalie'] == "" or settings.SERVER_CONFIG[guild]['attendance']['Goalie'] == interaction.user.display_name:
            user_name = interaction.user.display_name
            if user_name in self.player_tracking:
                msg = await interaction.channel.fetch_message(self.message_id)
                helper.clear_name(guild, user_name)
                self.player_tracking[user_name] = "In - G"
                await helper.send_line_up(guild, user_name, 'Goalie', interaction.channel, msg)
            else:
                if self.message_id == "":
                    self.message_id = await helper.send_line_up(guild, user_name, 'Goalie', interaction.channel, None)
                else:
                    msg = await interaction.channel.fetch_message(self.message_id)
                    await helper.send_line_up(guild, user_name, 'Goalie', interaction.channel, msg)
            self.player_tracking[user_name] = "In - G"
        else:
            await interaction.channel.send("A Goalie is already selected. He will have to move positions before a new goalie can be selected")

    
    @discord.ui.button(label="Maybe", style=discord.ButtonStyle.grey, custom_id="maybe")
    async def maybe_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name

        user_name = interaction.user.display_name
        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)
            helper.clear_name(guild,user_name)
            self.player_tracking[user_name] = "Maybe"
            await helper.send_line_up(guild, user_name, 'Maybe', interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await helper.send_line_up(guild, user_name, 'Maybe', interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await helper.send_line_up(guild, user_name, 'Maybe', interaction.channel, msg)
            self.player_tracking[user_name] = "Maybe"

    @discord.ui.button(label="Out", style=discord.ButtonStyle.red, custom_id="out")
    async def out_button_callback(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild.name

        user_name = interaction.user.display_name
        if user_name in self.player_tracking:
            msg = await interaction.channel.fetch_message(self.message_id)

            helper.clear_name(guild,user_name)

            self.player_tracking[user_name] = "Out"
            await helper.send_line_up(guild, user_name, 'Out', interaction.channel, msg)
        else:
            if self.message_id == "":
                self.message_id = await helper.send_line_up(guild, user_name, 'Out', interaction.channel, None)
            else:
                msg = await interaction.channel.fetch_message(self.message_id)
                await helper.send_line_up(guild, user_name, 'Out', interaction.channel, msg)
            self.player_tracking[user_name] = "Out"