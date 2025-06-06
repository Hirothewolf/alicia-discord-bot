import nextcord
from nextcord.ui import Modal, TextInput
import random
from typing import List, Optional
import asyncio
import aiohttp

class APIManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    async def create_api_modal(self, guild_id: str, current_api_keys: List[str]):
        return APIModal(self, guild_id, current_api_keys)

    async def get_api_key(self, guild_id: str) -> Optional[str]:
        guild_config = await self.config_manager.get_guild_config(str(guild_id))
        api_keys = guild_config.get('api_keys', [])
        
        if not api_keys:
            return None
        
        return random.choice(api_keys)

    async def handle_api_error(self, guild_id: str, error_api_key: str) -> Optional[str]:
        guild_config = await self.config_manager.get_guild_config(str(guild_id))
        api_keys = guild_config.get('api_keys', [])
        
        print(f"API Error occurred with key ending in ...{error_api_key[-4:]} for guild {guild_id}")
        
        remaining_keys = [key for key in api_keys if key != error_api_key]
        if remaining_keys:
            new_key = random.choice(remaining_keys)
            await self.config_manager.update_guild_config(str(guild_id), 'api_keys', remaining_keys)
            return new_key
        else:
            print(f"No more API keys available for guild {guild_id}")
            return None

    async def notify_admins_about_api_error(self, guild: nextcord.Guild, error_api_key: str, channel: nextcord.TextChannel):
        embed = nextcord.Embed(
            title="API Error",
            description=f"An API error occurred with a key ending in ...{error_api_key[-4:]}",
            color=nextcord.Color.red()
        )
        embed.add_field(name="Guild", value=guild.name)
        embed.add_field(name="Action Required", value="Please check and update the API key if necessary.")
        
        message = await channel.send(embed=embed)
        
        # Delete the message after 10 seconds
        await asyncio.sleep(10)
        try:
            await message.delete()
        except nextcord.errors.NotFound:
            pass  # Message might have been deleted already

    async def send_api_error_notification(self, guild: nextcord.Guild, error_api_key: str):
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await self.notify_admins_about_api_error(guild, error_api_key, channel)
                    break
                except nextcord.errors.Forbidden:
                    continue

    async def handle_api_error_and_notify(self, guild: nextcord.Guild, error_api_key: str) -> Optional[str]:
        new_key = await self.handle_api_error(str(guild.id), error_api_key)
        await self.send_api_error_notification(guild, error_api_key)
        return new_key

    async def validate_api_key(self, api_key: str) -> bool:
        url = "https://generativelanguage.googleapis.com/v1beta/models?key=" + api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200

class APIModal(Modal, title='API Key Manager'):
    def __init__(self, api_manager: APIManager, guild_id: str, current_api_keys: List[str]):
        super().__init__()
        self.api_manager = api_manager
        self.guild_id = guild_id
        
        current_keys_str = ', '.join(current_api_keys)
        
        self.api_keys = TextInput(
            label='API Key',
            style=nextcord.TextStyle.paragraph,
            required=True,
            placeholder="Enter new API key or modify existing one",
            max_length=1000,
            default=current_keys_str
        )
        self.add_item(self.api_keys)

    async def on_submit(self, interaction: nextcord.Interaction):
        new_api_keys = [key.strip() for key in self.api_keys.value.split(',') if key.strip()]

        if not new_api_keys:
            embed = nextcord.Embed(title="Error", description="No API key provided. Please enter an API key.", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(new_api_keys) > 10:
            embed = nextcord.Embed(title="Error", description="You can only add up to 10 API keys.", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        valid_keys = []
        invalid_keys = []
        for key in new_api_keys:
            if await self.api_manager.validate_api_key(key):
                valid_keys.append(key)
            else:
                invalid_keys.append(key)

        if valid_keys:
            await self.api_manager.config_manager.update_guild_config(str(self.guild_id), 'api_keys', valid_keys)
            embed = nextcord.Embed(title="Success", description=f"Successfully updated API keys for this guild. Your new API keys are now active.", color=nextcord.Color.green())
        else:
            embed = nextcord.Embed(title="Error", description="No valid API keys were provided.", color=nextcord.Color.red())

        if invalid_keys:
            embed.add_field(name="Invalid Keys", value=f"The following keys were invalid and not added: {', '.join(invalid_keys)}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(tree, config_manager):
    api_manager = APIManager(config_manager)
    # You can add any commands related to API management here
    return api_manager