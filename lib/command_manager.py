import nextcord
from nextcord import app_commands
from typing import List, Dict, Any
from lib.config_manager import ConfigManager
from lib.model_manager import ModelManager # type: ignore
from lib.guild_interaction_db import GuildHistoryManager # type: ignore
from lib.api_manager import APIManager
from lib.error_handler import ErrorHandler

class SettingsView(nextcord.ui.View):
    def __init__(self, command_manager):
        super().__init__(timeout=300)
        self.command_manager = command_manager

    @nextcord.ui.button(label="General Settings", style=nextcord.ButtonStyle.primary)
    async def general_settings(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.command_manager.show_general_settings(interaction)

    @nextcord.ui.button(label="Safety Settings", style=nextcord.ButtonStyle.primary)
    async def safety_settings(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.command_manager.show_safety_settings(interaction)

    @nextcord.ui.button(label="Channel Management", style=nextcord.ButtonStyle.primary)
    async def channel_management(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.command_manager.show_channel_management(interaction)

    @nextcord.ui.button(label="Model Selection", style=nextcord.ButtonStyle.primary)
    async def model_selection(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.command_manager.model_manager.show_model_selector(interaction, str(interaction.guild_id))

    @nextcord.ui.button(label="Clear History", style=nextcord.ButtonStyle.danger)
    async def clear_history(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.command_manager.clear_history(interaction)

class CommandManager:
    def __init__(self, tree: app_commands.CommandTree, config_manager: ConfigManager, 
                 model_manager: ModelManager, guild_history_manager: GuildHistoryManager, 
                 api_manager: APIManager, error_handler: ErrorHandler, bot: nextcord.Client):
        self.tree = tree
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.guild_history_manager = guild_history_manager
        self.api_manager = api_manager
        self.error_handler = error_handler
        self.bot = bot

    async def setup_commands(self):
        await self.setup_settings_command()
        await self.api_manager.setup(self.tree, self.config_manager)

    async def setup_settings_command(self):
        @self.tree.command(name="settings", description="Access and modify bot settings")
        @app_commands.checks.has_permissions(administrator=True)
        async def settings(interaction: nextcord.Interaction):
            await self.show_settings_menu(interaction)

    async def show_settings_menu(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(title="Bot Settings", description="Please select a category to modify:", color=nextcord.Color.blue())
        view = SettingsView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def show_general_settings(self, interaction: nextcord.Interaction):
        guild_id = str(interaction.guild_id)
        config = await self.config_manager.get_guild_config(guild_id)
        
        class GeneralSettingsView(nextcord.ui.View):
            def __init__(self, command_manager):
                super().__init__()
                self.command_manager = command_manager

            @nextcord.ui.button(label="Toggle RP Mode", style=nextcord.ButtonStyle.primary)
            async def toggle_rp_mode(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
                new_value = not config.get("rp_mode_enabled", False)
                await self.command_manager.config_manager.update_guild_config(guild_id, "rp_mode_enabled", new_value)
                await interaction.response.send_message(f"RP Mode has been {'enabled' if new_value else 'disabled'}.", ephemeral=True)

            @nextcord.ui.button(label="Toggle Mention Requirement", style=nextcord.ButtonStyle.primary)
            async def toggle_mention_requirement(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
                new_value = not config.get("require_mention", False)
                await self.command_manager.config_manager.update_guild_config(guild_id, "require_mention", new_value)
                await interaction.response.send_message(f"Mention requirement has been {'enabled' if new_value else 'disabled'}.", ephemeral=True)

            @nextcord.ui.button(label="Modify System Instruction", style=nextcord.ButtonStyle.primary)
            async def modify_system_instruction(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
                modal = SystemInstructionModal(self.command_manager.config_manager, guild_id)
                await interaction.response.send_modal(modal)

        embed = nextcord.Embed(title="General Settings", description="Modify general bot settings:", color=nextcord.Color.green())
        embed.add_field(name="RP Mode", value="Enabled" if config.get("rp_mode_enabled", False) else "Disabled", inline=False)
        embed.add_field(name="Mention Requirement", value="Enabled" if config.get("require_mention", False) else "Disabled", inline=False)
        embed.add_field(name="System Instruction", value=config.get("system_instruction", "Not set")[:1024], inline=False)

        view = GeneralSettingsView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def show_safety_settings(self, interaction: nextcord.Interaction):
        await self.safety_command.display_current_settings(interaction)

    async def show_channel_management(self, interaction: nextcord.Interaction):
        guild_id = str(interaction.guild_id)
        config = await self.config_manager.get_guild_config(guild_id)
        allowed_channels = config.get("allowed_channels", [])

        embed = nextcord.Embed(title="Channel Management", description="Manage allowed channels:", color=nextcord.Color.green())
        for channel_id in allowed_channels:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                embed.add_field(name=channel.name, value=f"ID: {channel_id}", inline=False)

        class ChannelManagementView(nextcord.ui.View):
            def __init__(self, command_manager):
                super().__init__()
                self.command_manager = command_manager

            @nextcord.ui.button(label="Add Channel", style=nextcord.ButtonStyle.green)
            async def add_channel(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
                modal = AddChannelModal(self.command_manager, guild_id)
                await interaction.response.send_modal(modal)

            @nextcord.ui.button(label="Remove Channel", style=nextcord.ButtonStyle.red)
            async def remove_channel(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
                modal = RemoveChannelModal(self.command_manager, guild_id)
                await interaction.response.send_modal(modal)

        view = ChannelManagementView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def clear_history(self, interaction: nextcord.Interaction):
        guild_id = str(interaction.guild_id)
        await self.guild_history_manager.clear_guild_history(guild_id)
        await interaction.response.send_message("Chat history has been cleared.", ephemeral=True)

class SystemInstructionModal(nextcord.ui.Modal, title="Modify System Instruction"):
    def __init__(self, config_manager, guild_id):
        super().__init__()
        self.config_manager = config_manager
        self.guild_id = guild_id
        self.instruction = nextcord.ui.TextInput(
            label="New System Instruction",
            style=nextcord.TextStyle.paragraph,
            placeholder="Enter the new system instruction here...",
            required=True,
            max_length=1000
        )
        self.add_item(self.instruction)

    async def on_submit(self, interaction: nextcord.Interaction):
        await self.config_manager.update_guild_config(self.guild_id, "system_instruction", self.instruction.value)
        await interaction.response.send_message("System instruction updated successfully.", ephemeral=True)

class AddChannelModal(nextcord.ui.Modal, title="Add Channel"):
    def __init__(self, command_manager, guild_id):
        super().__init__()
        self.command_manager = command_manager
        self.guild_id = guild_id
        self.channel_id = nextcord.ui.TextInput(
            label="Channel ID",
            placeholder="Enter the ID of the channel to add",
            required=True
        )
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: nextcord.Interaction):
        channel_id = int(self.channel_id.value)
        config = await self.command_manager.config_manager.get_guild_config(self.guild_id)
        allowed_channels = config.get("allowed_channels", [])
        if channel_id not in allowed_channels:
            allowed_channels.append(channel_id)
            await self.command_manager.config_manager.update_guild_config(self.guild_id, "allowed_channels", allowed_channels)
            await interaction.response.send_message(f"Channel <#{channel_id}> added to allowed channels.", ephemeral=True)
        else:
            await interaction.response.send_message("This channel is already in the allowed list.", ephemeral=True)

class RemoveChannelModal(nextcord.ui.Modal, title="Remove Channel"):
    def __init__(self, command_manager, guild_id):
        super().__init__()
        self.command_manager = command_manager
        self.guild_id = guild_id
        self.channel_id = nextcord.ui.TextInput(
            label="Channel ID",
            placeholder="Enter the ID of the channel to remove",
            required=True
        )
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: nextcord.Interaction):
        channel_id = int(self.channel_id.value)
        config = await self.command_manager.config_manager.get_guild_config(self.guild_id)
        allowed_channels = config.get("allowed_channels", [])
        if channel_id in allowed_channels:
            allowed_channels.remove(channel_id)
            await self.command_manager.config_manager.update_guild_config(self.guild_id, "allowed_channels", allowed_channels)
            await interaction.response.send_message(f"Channel <#{channel_id}> removed from allowed channels.", ephemeral=True)
        else:
            await interaction.response.send_message("This channel is not in the allowed list.", ephemeral=True)