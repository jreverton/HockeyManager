from pprint import pprint
import discord
import helper
import settings

from discord.ui import View
from discord.emoji import Emoji

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
