import discord
from discord import app_commands
from typing import List

async def setup(tree: app_commands.CommandTree):
    @tree.command(name="filter_safety", description="Set the safety settings for Gemini models")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        category="Safety category to configure",
        level="Safety level to set"
    )
    async def set_safety(interaction: discord.Interaction, category: str, level: str):
        guild_id = str(interaction.guild_id)
        config = await interaction.client.config_manager.get_guild_config(guild_id)
        
        # Check if current provider supports safety settings
        current_provider = config.get("ai_provider", "gemini")
        if not interaction.client.provider_manager.supports_safety_settings(current_provider):
            embed = discord.Embed(
                title="Safety Settings Not Supported",
                description=f"The current provider ({current_provider}) does not support safety settings. Safety settings are only available for Google Gemini models.",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if "safety_settings" not in config:
            config["safety_settings"] = {}

        category_upper = category.upper()
        config["safety_settings"][category_upper] = level

        try:
            await interaction.client.config_manager.save_guild_config(guild_id, config)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while saving the configuration: {str(e)}", ephemeral=True)
            return

        # Improved confirmation message
        category_name = get_readable_category_name(category_upper)
        level_name = get_readable_level_name(level)
        
        embed = discord.Embed(
            title="Safety Setting Updated",
            description=f"The safety filter for **{category_name}** has been set to **{level_name}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Category", value=category_name, inline=True)
        embed.add_field(name="New Level", value=level_name, inline=True)
        embed.set_footer(text="This setting will be applied to all future conversations with Gemini models.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_safety.autocomplete("category")
    async def category_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        choices = [
            app_commands.Choice(name="Sexually Explicit", value="HARM_CATEGORY_SEXUALLY_EXPLICIT"),
            app_commands.Choice(name="Hate Speech", value="HARM_CATEGORY_HATE_SPEECH"),
            app_commands.Choice(name="Harassment", value="HARM_CATEGORY_HARASSMENT"),
            app_commands.Choice(name="Dangerous Content", value="HARM_CATEGORY_DANGEROUS_CONTENT")
        ]
        
        return choices

    @set_safety.autocomplete("level")
    async def level_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name="Minimal Detection", value="BLOCK_NONE"),
            app_commands.Choice(name="Low Detection", value="BLOCK_ONLY_HIGH"),
            app_commands.Choice(name="Normal Detection", value="BLOCK_MEDIUM_AND_ABOVE"),
            app_commands.Choice(name="High Detection", value="BLOCK_LOW_AND_ABOVE")
        ]

def get_readable_category_name(category: str) -> str:
    return {
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "Sexually Explicit Content",
        "HARM_CATEGORY_HATE_SPEECH": "Hate Speech",
        "HARM_CATEGORY_HARASSMENT": "Harassment",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "Dangerous Content"
    }.get(category, category)

def get_readable_level_name(level: str) -> str:
    return {
        "BLOCK_NONE": "Minimal Detection",
        "BLOCK_ONLY_HIGH": "Low Detection",
        "BLOCK_MEDIUM_AND_ABOVE": "Normal Detection",
        "BLOCK_LOW_AND_ABOVE": "High Detection"
    }.get(level, level)

async def display_current_settings(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    config = await interaction.client.config_manager.get_guild_config(guild_id)
    current_provider = config.get("ai_provider", "gemini")
    
    if not interaction.client.provider_manager.supports_safety_settings(current_provider):
        embed = discord.Embed(
            title="Safety Settings Not Available",
            description=f"The current provider ({current_provider}) does not support safety settings. Safety settings are only available for Google Gemini models.",
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    safety_settings = config.get("safety_settings", {})

    embed = discord.Embed(
        title="Current Safety Settings (Gemini Only)",
        description="Here are the current safety filter settings for Gemini models:",
        color=discord.Color.blue()
    )

    for category, level in safety_settings.items():
        category_name = get_readable_category_name(category)
        level_name = get_readable_level_name(level)
        embed.add_field(name=category_name, value=level_name, inline=False)

    if not safety_settings:
        embed.description = "No safety settings have been configured yet for Gemini models."

    await interaction.response.send_message(embed=embed, ephemeral=True)