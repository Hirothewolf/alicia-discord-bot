import nextcord
from nextcord import app_commands
from nextcord.ui import Button, View
import json
import asyncio
from typing import Dict, Any, Callable
import os

from lib.config_manager import ConfigManager

MAX_FILE_SIZE = 150000  # Limite máximo de caracteres

class ConfirmView(View):
    def __init__(self, callback: Callable[[nextcord.Interaction, bool], None]):
        super().__init__(timeout=60)
        self.callback = callback

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.danger)
    async def confirm(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.callback(interaction, True)

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.secondary)
    async def cancel(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        await self.callback(interaction, False)

async def import_system_instruction(interaction: nextcord.Interaction, content: str):
    guild_id = str(interaction.guild_id)
    config = await interaction.client.config_manager.get_guild_config(guild_id)

    async def confirmation_callback(confirm_interaction: nextcord.Interaction, confirmed: bool):
        if confirmed:
            config["system_instruction"] = content
            config["custom_instruction_imported"] = True
            await interaction.client.config_manager.save_guild_config(guild_id, config)
            embed = nextcord.Embed(
                title="System Instruction Imported",
                description="System instruction successfully imported and updated.",
                color=nextcord.Color.green()
            )
            await confirm_interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = nextcord.Embed(
                title="Import Cancelled",
                description="Import cancelled.",
                color=nextcord.Color.red()
            )
            await confirm_interaction.response.send_message(embed=embed, ephemeral=True)

    view = ConfirmView(confirmation_callback)
    embed = nextcord.Embed(
        title="Warning",
        description="Warning: Importing this system instruction will replace the current one. This action cannot be undone. Do you want to proceed?",
        color=nextcord.Color.yellow()
    )
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

def extract_content_from_json(json_content: str) -> str:
    try:
        json_data = json.loads(json_content)
    except json.JSONDecodeError:
        return json_content

    if isinstance(json_data, str):
        return json_data
    elif "char_name" in json_data:  # Provável Character Card V2
        return json_data.get("char_persona", "")
    elif "description" in json_data:  # Possível formato W++
        return json_data.get("description", "")
    else:
        # Se não for um formato reconhecido, usa o conteúdo completo
        return json.dumps(json_data)

async def setup(tree: app_commands.CommandTree):
    @tree.command(name="import_instruction", description="Import a custom system instruction from a file")
    @app_commands.checks.has_permissions(administrator=True)
    async def import_instruction(interaction: nextcord.Interaction, file: nextcord.Attachment):
        await interaction.response.defer(ephemeral=True)

        if not file.filename.endswith(('.txt', '.json')):
            embed = nextcord.Embed(
                title="Error",
                description="Please upload a .txt or .json file.",
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if file.size > MAX_FILE_SIZE:
            embed = nextcord.Embed(
                title="Error",
                description=f"File is too large. Maximum size is {MAX_FILE_SIZE} characters.",
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            content = await file.read()
            content = content.decode('utf-8')

            if file.filename.endswith('.json'):
                content = extract_content_from_json(content)

            if len(content) > MAX_FILE_SIZE:
                embed = nextcord.Embed(
                    title="Error",
                    description=f"Extracted content is too large. Maximum size is {MAX_FILE_SIZE} characters.",
                    color=nextcord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            await import_system_instruction(interaction, content)

        except UnicodeDecodeError:
            embed = nextcord.Embed(
                title="Error",
                description="Unable to read the file. Please ensure it's a valid text file.",
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = nextcord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)