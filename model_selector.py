import discord
from discord.ui import View
import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta
import asyncio
from api_manager import get_api_key

CACHE_FILE = 'models_cache.json'

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        if datetime.now() - datetime.fromisoformat(cache['timestamp']) < timedelta(weeks=1):
            return cache['models']
    return None

def save_cache(models):
    cache = {
        'timestamp': datetime.now().isoformat(),
        'models': models
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

async def get_models(guild_id):
    cached_models = load_cache()
    if cached_models:
        return cached_models
    
    api_key = await get_api_key(guild_id)
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
    
    save_cache(models)
    return models

class ModelSelector(discord.ui.View):
    def __init__(self, models, config, save_function, guild_id):
        super().__init__(timeout=300)
        self.models = models
        self.current_page = 0
        self.config = config
        self.save_function = save_function
        self.guild_id = guild_id

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.models)
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    @discord.ui.button(label="Select This Model", style=discord.ButtonStyle.green)
    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_model = self.models[self.current_page]['name']
        self.config["model_name"] = selected_model
        await self.save_function()
        
        embed = discord.Embed(
            title="Model Updated",
            description=f"Model set to {selected_model}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Delete the message after 10 seconds
        await asyncio.sleep(10)
        await interaction.delete_original_response()
        
        self.stop()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.models)
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    def get_current_embed(self):
        model = self.models[self.current_page]
        current_model = self.config.get("model_name", "Not set")
        
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

# Function to setup the model selector command
def setup_model_selector(tree, get_guild_config, save_guild_configs):
    @tree.command(name="models", description="Select a Gemini model for the bot to use")
    async def select_model(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_config = get_guild_config(guild_id)
        
        try:
            models = await get_models(guild_id)
            view = ModelSelector(models, guild_config, save_guild_configs, guild_id)
            await interaction.response.send_message(embed=view.get_current_embed(), view=view, ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while retrieving models: {str(e)}", ephemeral=True)
