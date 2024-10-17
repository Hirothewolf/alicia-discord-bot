import discord
from discord import app_commands
from discord.ui import Select, View
from typing import List, Dict, Any
import asyncio

class ChannelSelect(Select):
    def __init__(self, channels: List[discord.TextChannel], action: str):
        options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]
        super().__init__(placeholder="Select a channel...", min_values=1, max_values=1, options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        channel_id = int(self.values[0])
        config = await interaction.client.config_manager.get_guild_config(str(interaction.guild_id))

        if self.action == "add":
            if channel_id not in config["allowed_channels"]:
                config["allowed_channels"].append(channel_id)
                await interaction.client.config_manager.save_guild_config(str(interaction.guild_id), config)
                embed = discord.Embed(title="Channel Added", description=f"Added <#{channel_id}> to allowed channels", color=discord.Color.green())
            else:
                embed = discord.Embed(title="Channel Already Allowed", description=f"<#{channel_id}> is already an allowed channel", color=discord.Color.yellow())
        else:  # remove
            if channel_id in config["allowed_channels"]:
                config["allowed_channels"].remove(channel_id)
                await interaction.client.config_manager.save_guild_config(str(interaction.guild_id), config)
                embed = discord.Embed(title="Channel Removed", description=f"Removed <#{channel_id}> from allowed channels", color=discord.Color.green())
            else:
                embed = discord.Embed(title="Channel Not in List", description=f"<#{channel_id}> is not in the allowed channels list", color=discord.Color.yellow())

        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

class ChannelSelectView(View):
    def __init__(self, channels: List[discord.TextChannel], action: str):
        super().__init__()
        self.add_item(ChannelSelect(channels, action))

async def setup(tree: app_commands.CommandTree):
    @tree.command(name="manage_allowed_channel", description="Add or remove allowed channels")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        action="Add or remove a channel",
        channel_name="Start typing to search for a channel"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add Channel", value="add"),
        app_commands.Choice(name="Remove Channel", value="remove")
    ])
    async def manage_allowed_channel(
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        channel_name: str
    ):
        matching_channels = [
            channel for channel in interaction.guild.channels
            if channel_name.lower() in channel.name.lower() and isinstance(channel, discord.TextChannel)
        ]

        if not matching_channels:
            embed = discord.Embed(
                title="No Channels Found",
                description=f"No channels matching '{channel_name}' were found.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        view = ChannelSelectView(matching_channels, action.value)
        embed = discord.Embed(
            title=f"Select Channel to {action.name}",
            description="Choose a channel from the dropdown menu:",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)