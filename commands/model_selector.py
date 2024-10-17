import discord
from discord.ui import View
import google.generativeai as genai
import os
import json
import aiofiles
import asyncio
from lib.api_manager import APIManager
from lib.config_manager import ConfigManager
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

CACHE_FILE = 'models_cache.json'

async def load_cache() -> Optional[List[Dict[str, Any]]]:
    if os.path.exists(CACHE_FILE):
        async with aiofiles.open(CACHE_FILE, 'r') as f:
            cache = json.loads(await f.read())
        if datetime.now() - datetime.fromisoformat(cache['timestamp']) < timedelta(weeks=1):
            return cache['models']
    return None

async def save_cache(models: List[Dict[str, Any]]) -> None:
    cache = {
        'timestamp': datetime.now().isoformat(),
        'models': models
    }
    async with aiofiles.open(CACHE_FILE, 'w') as f:
        await f.write(json.dumps(cache, indent=4))

async def get_models(guild_id: str, api_manager: APIManager) -> List[Dict[str, Any]]:
    cached_models = await load_cache()
    if cached_models:
        return cached_models
    
    api_key = await api_manager.get_api_key(guild_id)
    if not api_key:
        raise ValueError("No valid API key found for this guild.")
    
    genai.configure(api_key=api_key)
    
    models = []
    for model in genai.list_models():
        if model.name.startswith("models/gemini-"):
            model_data = {
                'name': model.name.split('models/')[1],
                'base_model_id': getattr(model, 'base_model_id', 'N/A'),
                'version': getattr(model, 'version', 'N/A'),
                'display_name': model.display_name,
                'description': model.description,
                'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
                'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
                'supported_generation_methods': model.supported_generation_methods,
                'temperature': getattr(model, 'temperature', 'N/A'),
                'max_temperature': getattr(model, 'max_temperature', 'N/A'),
                'top_p': getattr(model, 'top_p', 'N/A'),
                'top_k': getattr(model, 'top_k', 'N/A')
            }
            models.append(model_data)
    
    await save_cache(models)
    return models

class ModelSelector(discord.ui.View):
    def __init__(self, models: List[Dict[str, Any]], guild_id: str, config_manager: ConfigManager):
        super().__init__(timeout=300)
        self.models = models
        self.current_page = 0
        self.guild_id = guild_id
        self.config_manager = config_manager

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.models)
        await interaction.response.edit_message(embed=await self.get_current_embed(), view=self)

    @discord.ui.button(label="Select This Model", style=discord.ButtonStyle.green)
    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_model = self.models[self.current_page]['name']
        await self.config_manager.update_guild_config(self.guild_id, "model_name", selected_model)
        
        embed = discord.Embed(
            title="Model Updated",
            description=f"Model set to {selected_model}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await asyncio.sleep(10)
        await interaction.delete_original_response()
        
        self.stop()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.models)
        await interaction.response.edit_message(embed=await self.get_current_embed(), view=self)

    async def get_current_embed(self) -> discord.Embed:
        model = self.models[self.current_page]
        config = await self.config_manager.get_guild_config(self.guild_id)
        current_model = config.get("model_name", "Not set")
        
        embed = discord.Embed(
            title=model['display_name'],
            description=model['description'],
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Current Model", value=f"```{current_model}```", inline=True)
        embed.add_field(name="Model Name", value=f"```{model['name']}```", inline=True)
        embed.add_field(name="Version", value=f"```{model['version']}```", inline=True)
        embed.add_field(name="Input Token Limit", value=f"```{model['input_token_limit']}```", inline=True)
        embed.add_field(name="Output Token Limit", value=f"```{model['output_token_limit']}```", inline=True)
        embed.add_field(name="Generation Methods", value=f"```{', '.join(model['supported_generation_methods'])}```", inline=False)
        embed.add_field(name="Temperature", value=f"```{model['temperature']}```", inline=True)
        embed.add_field(name="Max Temperature", value=f"```{model['max_temperature']}```", inline=True)
        embed.add_field(name="Top P", value=f"```{model['top_p']}```", inline=True)
        embed.add_field(name="Top K", value=f"```{model['top_k']}```", inline=True)
        embed.set_footer(text=f"Gemini Model {self.current_page + 1} of {len(self.models)}")
        return embed

async def show_model_selector(interaction: discord.Interaction, guild_id: str, api_manager: APIManager, config_manager: ConfigManager):
    try:
        models = await get_models(guild_id, api_manager)
        view = ModelSelector(models, guild_id, config_manager)
        await interaction.response.send_message(embed=await view.get_current_embed(), view=view, ephemeral=True)
    except ValueError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while retrieving models: {str(e)}", ephemeral=True)