import nextcord
from nextcord.ui import View
from typing import List, Dict, Any, Optional
from lib.api_manager import APIManager
from lib.config_manager import ConfigManager
from lib.provider_manager import ProviderManager
import asyncio

class ModelSelector(nextcord.ui.View):
    def __init__(self, models: List[Dict[str, Any]], guild_id: str, config_manager: ConfigManager, provider_name: str):
        super().__init__(timeout=300)
        self.models = models
        self.current_page = 0
        self.guild_id = guild_id
        self.config_manager = config_manager
        self.provider_name = provider_name

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.gray)
    async def previous_button(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.models)
        await interaction.response.edit_message(embed=await self.get_current_embed(), view=self)

    @nextcord.ui.button(label="Select This Model", style=nextcord.ButtonStyle.green)
    async def select_button(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        selected_model = self.models[self.current_page]['name']
        
        # Update both the general model_name and provider-specific model
        await self.config_manager.update_guild_config(self.guild_id, "model_name", selected_model)
        
        # Update provider-specific settings
        config = await self.config_manager.get_guild_config(self.guild_id)
        provider_settings = config.get("provider_settings", {})
        if self.provider_name not in provider_settings:
            provider_settings[self.provider_name] = {}
        provider_settings[self.provider_name]["model_name"] = selected_model
        await self.config_manager.update_guild_config(self.guild_id, "provider_settings", provider_settings)
        
        embed = nextcord.Embed(
            title="Model Updated",
            description=f"Model set to {selected_model} for {self.provider_name}",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await asyncio.sleep(10)
        await interaction.delete_original_response()
        
        self.stop()

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.gray)
    async def next_button(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.models)
        await interaction.response.edit_message(embed=await self.get_current_embed(), view=self)

    async def get_current_embed(self) -> nextcord.Embed:
        model = self.models[self.current_page]
        config = await self.config_manager.get_guild_config(self.guild_id)
        current_model = config.get("model_name", "Not set")
        
        embed = nextcord.Embed(
            title=model.get('display_name', model['name']),
            description=model.get('description', 'No description available'),
            color=nextcord.Color.blue()
        )
        
        embed.add_field(name="Current Model", value=f"```{current_model}```", inline=True)
        embed.add_field(name="Model Name", value=f"```{model['name']}```", inline=True)
        embed.add_field(name="Provider", value=f"```{self.provider_name}```", inline=True)
        
        if 'input_token_limit' in model:
            embed.add_field(name="Input Token Limit", value=f"```{model['input_token_limit']}```", inline=True)
        if 'output_token_limit' in model:
            embed.add_field(name="Output Token Limit", value=f"```{model['output_token_limit']}```", inline=True)
        if 'context_length' in model:
            embed.add_field(name="Context Length", value=f"```{model['context_length']}```", inline=True)
        
        embed.set_footer(text=f"Model {self.current_page + 1} of {len(self.models)} | Provider: {self.provider_name}")
        return embed

async def show_model_selector(interaction: nextcord.Interaction, guild_id: str, api_manager: APIManager, config_manager: ConfigManager, provider_manager: ProviderManager):
    try:
        config = await config_manager.get_guild_config(guild_id)
        current_provider = config.get("ai_provider", "gemini")
        
        api_key = await api_manager.get_api_key(guild_id)
        if not api_key:
            await interaction.response.send_message("No valid API key found for this guild.", ephemeral=True)
            return
        
        models = await provider_manager.get_available_models(current_provider, api_key)
        if not models:
            models = provider_manager.get_static_models(current_provider)
        
        view = ModelSelector(models, guild_id, config_manager, current_provider)
        await interaction.response.send_message(embed=await view.get_current_embed(), view=view, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while retrieving models: {str(e)}", ephemeral=True)