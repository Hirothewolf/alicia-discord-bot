import discord
from discord import app_commands
from discord.ui import Button, View
import asyncio
from typing import Dict, Any, Callable

from commands.config_command import ConfigModal, SystemInstructionModal
from commands.model_selector import show_model_selector
from lib.config_manager import ConfigManager
from lib.api_manager import APIManager
from lib.provider_manager import ProviderManager

class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class ConfirmView(PersistentView):
    def __init__(self, callback: Callable[[discord.Interaction, bool], None]):
        super().__init__()
        self.callback = callback

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_button")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback(interaction, True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_button")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback(interaction, False)

class ExtraView(PersistentView):
    def __init__(self, bot, config_manager: ConfigManager, api_manager: APIManager, provider_manager: ProviderManager):
        super().__init__()
        self.bot = bot
        self.config_manager = config_manager
        self.api_manager = api_manager
        self.provider_manager = provider_manager

    async def handle_interaction(self, interaction: discord.Interaction, action: Callable):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You need administrator permissions to use this button.", ephemeral=True)
            return
        await action(interaction)

    @discord.ui.button(label="Clear Context", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="clear_context_button")
    async def clear_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.clear_history_action)

    async def clear_history_action(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        history = await self.bot.guild_history_manager.get_guild_history(guild_id)
        interaction_count = len(history)

        confirm_view = ConfirmView(self.clear_history_callback)
        embed = discord.Embed(
            title="Clear Chat Context",
            description=f"Are you sure you want to clear all {interaction_count} chat interactions from the bot's memory?\n\n**This action cannot be undone.**\n\n**Please confirm within 30 seconds or the process will be cancelled.**",
            color=discord.Color.red()
        )

        message = await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)
        await asyncio.sleep(30)
        await message.delete()

    async def clear_history_callback(self, interaction: discord.Interaction, confirmed: bool):
        if confirmed:
            guild_id = str(interaction.guild_id)
            await self.bot.guild_history_manager.clear_guild_history(guild_id)
            embed = discord.Embed(title="Chat Context Cleared", description="All chat interactions have been removed from the bot's memory.", color=discord.Color.green())
        else:
            embed = discord.Embed(title="Operation Cancelled", description="Chat Context clearing has been cancelled.", color=discord.Color.blue())
        message = await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(8)
        await message.delete()

    @discord.ui.button(label="Reset Guild Config", style=discord.ButtonStyle.danger, emoji="🔄", custom_id="reset_config_button")
    async def reset_guild_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.reset_guild_config_action)

    async def reset_guild_config_action(self, interaction: discord.Interaction):
        confirm_view = ConfirmView(self.reset_config_callback)
        embed = discord.Embed(
            title="Reset Guild Configuration",
            description="Are you sure you want to reset all guild settings to default?\n\n**This action cannot be undone.**",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

    async def reset_config_callback(self, interaction: discord.Interaction, confirmed: bool):
        if confirmed:
            guild_id = str(interaction.guild_id)
            default_config = await self.config_manager.load_or_create_default_config()
            
            # Preserve keys that shouldn't be reset
            current_config = await self.config_manager.get_guild_config(guild_id)
            preserved_keys = ['allowed_channels', 'api_keys']
            for key in preserved_keys:
                if key in current_config:
                    default_config[key] = current_config[key]
            
            # Update guild config with default settings
            await self.config_manager.save_guild_config(guild_id, default_config)
            
            embed = discord.Embed(
                title="Guild Configuration Reset",
                description="All guild settings have been reset to default values, except for allowed channels and API keys.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Operation Cancelled",
                description="Guild configuration reset has been cancelled.",
                color=discord.Color.blue()
            )
        message = await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(8)
        await message.delete()

    @discord.ui.button(label="Manage API Keys", style=discord.ButtonStyle.primary, emoji="🔑", custom_id="manage_api_keys_button")
    async def manage_api_keys(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.manage_api_keys_action)

    async def manage_api_keys_action(self, interaction: discord.Interaction):
        guild_config = await self.config_manager.get_guild_config(str(interaction.guild_id))
        current_api_keys = guild_config.get('api_keys', [])
        modal = await self.api_manager.create_api_modal(interaction.guild_id, current_api_keys)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Toggle RP Mode", style=discord.ButtonStyle.primary, emoji="🎭", custom_id="toggle_rp_mode_button")
    async def toggle_rp_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.toggle_rp_mode_action)

    async def toggle_rp_mode_action(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = await self.config_manager.get_guild_config(guild_id)
        new_rp_mode = not config.get("rp_mode_enabled", False)
        await self.config_manager.update_guild_config(guild_id, "rp_mode_enabled", new_rp_mode)
        status = "enabled" if new_rp_mode else "disabled"

        embed = discord.Embed(
            title="Role Play Mode Updated",
            description=f"Role Play mode has been {status} for this server.",
            color=discord.Color.green()
        )
        message = await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(8)
        await message.delete()

    @discord.ui.button(label="Toggle Mentions", style=discord.ButtonStyle.primary, emoji="💬", custom_id="toggle_mentions_button")
    async def toggle_mentions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.toggle_mentions_action)

    async def toggle_mentions_action(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = await self.config_manager.get_guild_config(guild_id)
        new_require_mention = not config.get("require_mention", False)
        await self.config_manager.update_guild_config(guild_id, "require_mention", new_require_mention)
        status = "required" if new_require_mention else "not required"

        embed = discord.Embed(
            title="Mention Requirement Updated",
            description=f"Mention is now {status} for the bot to respond",
            color=discord.Color.green()
        )
        message = await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(8)
        await message.delete()

    @discord.ui.button(label="LLM Settings", style=discord.ButtonStyle.primary, emoji="⚙️", custom_id="llm_settings_button")
    async def llm_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.llm_settings_action)

    async def llm_settings_action(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = await self.config_manager.get_guild_config(guild_id)
        modal = ConfigModal(config)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="System Instruction", style=discord.ButtonStyle.primary, emoji="📝", custom_id="system_instruction_button")
    async def system_instruction(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.system_instruction_action)

    async def system_instruction_action(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = await self.config_manager.get_guild_config(guild_id)

        if config.get("custom_instruction_imported", False):
            warning_embed = discord.Embed(
                title="Warning",
                description="A custom system instruction has been imported. Due to Discord limitations, "
                            "you can only edit these parameters before importing. If you continue, "
                            "the system instruction will revert to the default value. If you don't respond within 30 seconds, "
                            "it will be considered as refusing the confirmation.",
                color=discord.Color.yellow()
            )
            
            confirm_view = ConfirmView(self.system_instruction_callback)
            message = await interaction.response.send_message(embed=warning_embed, view=confirm_view, ephemeral=True)
            await asyncio.sleep(30)
            await message.delete()
        else:
            modal = SystemInstructionModal(config)
            await interaction.response.send_modal(modal)

    async def system_instruction_callback(self, interaction: discord.Interaction, confirmed: bool):
        if confirmed:
            guild_id = str(interaction.guild_id)
            default_config = await self.config_manager.get_guild_config("default")
            await self.config_manager.update_guild_config(guild_id, "system_instruction", default_config.get("system_instruction", ""))
            await self.config_manager.update_guild_config(guild_id, "custom_instruction_imported", False)
            
            new_config = await self.config_manager.get_guild_config(guild_id)
            modal = SystemInstructionModal(new_config)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Operation cancelled.", ephemeral=True)

    @discord.ui.button(label="Select Model", style=discord.ButtonStyle.primary, emoji="🤖", custom_id="select_model_button")
    async def select_model(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_interaction(interaction, self.select_model_action)

    async def select_model_action(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        await show_model_selector(interaction, guild_id, self.api_manager, self.config_manager, self.provider_manager)

async def setup_commands(tree: app_commands.CommandTree, bot, config_manager: ConfigManager, api_manager: APIManager, provider_manager: ProviderManager):
    @tree.command(name="settings", description="Access bot settings and actions")
    @app_commands.checks.has_permissions(administrator=True)
    async def extra(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Alicia Settings",
            description="Click the buttons below to access different settings and actions:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Clear Context 🗑️", value="Clear all chat interactions from bot memory", inline=True)
        embed.add_field(name="Toggle RP Mode 🎭", value="Enable or disable Role Play mode", inline=True)
        embed.add_field(name="Toggle Mentions 💬", value="Toggle whether the bot requires a mention to respond", inline=True)
        embed.add_field(name="LLM Settings ⚙️", value="Configure LLM parameters", inline=True)
        embed.add_field(name="System Instruction 📝", value="Set the system instruction for the bot", inline=True)
        embed.add_field(name="Select Model 🤖", value="Choose the AI model to use", inline=True)
        embed.add_field(name="Reset Guild Config 🔄", value="Reset all guild settings to default", inline=True)
        embed.add_field(name="Manage API Keys 🔑", value="Add or modify API keys", inline=True)
        
        guild_config = await config_manager.get_guild_config(str(interaction.guild_id))
        mention_status = "required" if guild_config.get("require_mention", False) else "not required"
        rp_status = "enabled" if guild_config.get("rp_mode_enabled", False) else "disabled"
        current_provider = guild_config.get("ai_provider", "gemini")
        current_model = guild_config.get("model_name", "Not set")
        
        embed.add_field(name="Current Provider 🔧", value=f"```{current_provider}```", inline=False)
        embed.add_field(name="Current Model 🤖", value=f"```{current_model}```", inline=False)
        embed.add_field(name="Mention Requirement 💬", value=f"```Currently {mention_status}```", inline=False)
        embed.add_field(name="Role Play Mode 🎭", value=f"```Currently {rp_status}```", inline=False)
        
        view = ExtraView(bot, config_manager, api_manager, provider_manager)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    # Add the persistent view to the bot
    bot.add_view(ExtraView(bot, config_manager, api_manager, provider_manager))