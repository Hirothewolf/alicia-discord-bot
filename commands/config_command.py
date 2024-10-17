import discord
from discord.ui import Modal, TextInput
from typing import Dict, Any
import asyncio
from lib.config_manager import ConfigManager

class ConfigModal(Modal, title="Configure Bot Settings"):
    temperature = TextInput(label="Temperature (0-2)", max_length=10, required=True)
    top_p = TextInput(label="Top P (0-1)", max_length=10, required=True)
    top_k = TextInput(label="Top K (0-100)", max_length=10, required=True)
    max_tokens = TextInput(label="Max Output Tokens (0-4096)", max_length=10, required=True)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.temperature.default = str(config.get("temperature", 1.0))
        self.top_p.default = str(config.get("top_p", 0.95))
        self.top_k.default = str(config.get("top_k", 64))
        self.max_tokens.default = str(config.get("max_output_tokens", 2048))

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        errors = []
        
        try:
            temp = float(self.temperature.value)
            if not 0 <= temp <= 2:
                errors.append("Temperature must be between 0 and 2")
            else:
                await interaction.client.config_manager.update_guild_config(guild_id, "temperature", temp)
        except ValueError:
            errors.append("Temperature must be a number")

        try:
            top_p = float(self.top_p.value)
            if not 0 <= top_p <= 1:
                errors.append("Top P must be between 0 and 1")
            else:
                await interaction.client.config_manager.update_guild_config(guild_id, "top_p", top_p)
        except ValueError:
            errors.append("Top P must be a number")

        try:
            top_k = int(self.top_k.value)
            if not 0 <= top_k <= 100:
                errors.append("Top K must be between 0 and 100")
            else:
                await interaction.client.config_manager.update_guild_config(guild_id, "top_k", top_k)
        except ValueError:
            errors.append("Top K must be an integer")

        try:
            max_tokens = int(self.max_tokens.value)
            if not 0 <= max_tokens <= 4096:
                errors.append("Max Output Tokens must be between 0 and 4096")
            else:
                await interaction.client.config_manager.update_guild_config(guild_id, "max_output_tokens", max_tokens)
        except ValueError:
            errors.append("Max Output Tokens must be an integer")

        if errors:
            error_message = "\n".join(errors)
            embed = discord.Embed(title="Configuration Error", description=error_message, color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Configuration Updated", description="Configuration updated successfully!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await asyncio.sleep(10)
        await interaction.delete_original_response()

class SystemInstructionModal(Modal, title="Configure System Instruction"):
    system_instruction = TextInput(label="System Instruction", style=discord.TextStyle.paragraph, required=True)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.system_instruction.default = config.get("system_instruction", "")

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        await interaction.client.config_manager.update_guild_config(guild_id, "system_instruction", self.system_instruction.value)
        embed = discord.Embed(title="System Instruction Updated", description="System Instruction updated successfully!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()