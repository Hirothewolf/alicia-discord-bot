import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import random
import asyncio

# Load guild configs
async def load_guild_configs():
    try:
        with open('guild_configs.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save guild configs
async def save_guild_configs(guild_configs):
    with open('guild_configs.json', 'w') as f:
        json.dump(guild_configs, f, indent=4)

class APIModal(Modal, title='API Key Manager'):
    def __init__(self, guild_id, current_api_keys):
        super().__init__()
        self.guild_id = guild_id
        
        current_keys_str = ', '.join(current_api_keys)
        
        self.api_keys = TextInput(
            label='API Key',
            style=discord.TextStyle.paragraph,
            required=True,
            placeholder="Enter new API key or modify existing one",
            max_length=1000,
            default=current_keys_str
        )
        self.add_item(self.api_keys)

    async def on_submit(self, interaction: discord.Interaction):
        guild_configs = await load_guild_configs()
        
        new_api_keys = [key.strip() for key in self.api_keys.value.split(',') if key.strip()]

        if not new_api_keys:
            embed = discord.Embed(title="Error", description="No API key provided. Please enter a API key.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(new_api_keys) > 10:
            embed = discord.Embed(title="Error", description="You can only add up to 10 API keys.(EXPERIMENTAL)", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if str(self.guild_id) not in guild_configs:
            guild_configs[str(self.guild_id)] = {}

        guild_configs[str(self.guild_id)]['api_keys'] = new_api_keys
        await save_guild_configs(guild_configs)

        embed = discord.Embed(title="Success", description=f"Successfully updated API key for this guild. Your new API key are now active.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.command(name="api_manager", description="Manage API key for this guild")
@app_commands.checks.has_permissions(administrator=True)
async def api_manager(interaction: discord.Interaction):
    guild_configs = await load_guild_configs()
    current_api_keys = guild_configs.get(str(interaction.guild_id), {}).get('api_keys', [])
    modal = APIModal(interaction.guild_id, current_api_keys)
    await interaction.response.send_modal(modal)

def setup(tree):
    tree.add_command(api_manager)

async def get_api_key(guild_id):
    guild_configs = await load_guild_configs()
    guild_config = guild_configs.get(str(guild_id), {})
    api_keys = guild_config.get('api_keys', [])
    
    if not api_keys:
        return None
    
    return random.choice(api_keys)

async def handle_api_error(guild_id, error_api_key):
    guild_configs = await load_guild_configs()
    guild_config = guild_configs.get(str(guild_id), {})
    api_keys = guild_config.get('api_keys', [])
    
    print(f"API Error occurred with key ending in ...{error_api_key[-4:]} for guild {guild_id}")
    
    remaining_keys = [key for key in api_keys if key != error_api_key]
    if remaining_keys:
        return random.choice(remaining_keys)
    else:
        print(f"No more API keys available for guild {guild_id}")
        return None

async def notify_admins_about_api_error(guild, error_api_key, channel):
    embed = discord.Embed(
        title="API Error",
        description=f"An API error occurred with a key ending in ...{error_api_key[-4:]}",
        color=discord.Color.red()
    )
    embed.add_field(name="Guild", value=guild.name)
    embed.add_field(name="Action Required", value="Please check and update the API key if necessary.")
    
    message = await channel.send(embed=embed)
    
    # Delete the message after 10 seconds
    await asyncio.sleep(10)
    try:
        await message.delete()
    except discord.errors.NotFound:
        pass  # Message might have been deleted already

async def send_api_error_notification(guild, error_api_key):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            try:
                await notify_admins_about_api_error(guild, error_api_key, channel)
                break
            except discord.errors.Forbidden:
                continue

# This function should be called from your main bot logic when an API error occurs
async def handle_api_error_and_notify(guild, error_api_key):
    new_key = await handle_api_error(guild.id, error_api_key)
    await send_api_error_notification(guild, error_api_key)
    return new_key