import nextcord
import os
import asyncio
from dotenv import load_dotenv
from nextcord.ext import commands
from typing import Dict, Any, Optional, List

from lib.alicia_presence_manager import AliciaPresenceManager
from lib.config_manager import ConfigManager
from lib.error_handler import ErrorHandler
from lib import guild_interaction_db
from lib.api_manager import APIManager
from lib.provider_manager import ProviderManager

from commands.settings_manager import setup_commands as setup_extra_commands
from commands.help_menu import setup_help_command
from commands.config_command import ConfigModal, SystemInstructionModal
from commands.safety_command import setup as setup_safety
from commands.channel_command import setup as setup_channel
from commands.import_instruction import setup as setup_import_instruction
from commands.provider_command import setup as setup_provider_command

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

class AliciaBot(nextcord.Client):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.dm_error_sent: Dict[int, bool] = {}
        self.sync_task = None

        # Initialize managers
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler()
        self.api_manager = APIManager(self.config_manager)
        self.provider_manager = ProviderManager()
        self.guild_history_manager = guild_interaction_db
        self.presence_manager = None

    async def setup_hook(self):
        # Load or create default config
        await self.config_manager.load_default_config()

        # Setup commands
        await setup_extra_commands(self, self.config_manager, self.api_manager, self.provider_manager)
        await setup_help_command(self)
        await setup_safety(self)
        await setup_channel(self)
        await setup_import_instruction(self)
        await setup_provider_command(self)

        # Initialize the AliciaPresenceManager
        self.presence_manager = AliciaPresenceManager(self)
        self.presence_manager.start()

        # Start periodic sync task
        self.sync_task = self.loop.create_task(self.periodic_sync())

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        await self.sync_all_guilds()

    async def sync_all_guilds(self):
        for guild in self.guilds:
            config = await self.config_manager.get_guild_config(str(guild.id))
            for channel_id in config.get("allowed_channels", []):
                await guild_interaction_db.sync_bot_user_messages(str(guild.id), channel_id, self)

    async def periodic_sync(self):
        while not self.is_closed():
            await self.sync_all_guilds()
            await asyncio.sleep(3600)  # Sync every hour

    async def close(self):
        if self.sync_task:
            self.sync_task.cancel()
        await super().close()

    async def on_message(self, message: nextcord.Message):
        if message.author == self.user:
            return

        if isinstance(message.channel, nextcord.DMChannel):
            if message.author.id not in self.dm_error_sent:
                await message.channel.send("Sorry, Alicia is not available for use in direct messages")
                self.dm_error_sent[message.author.id] = True
            return

        await self.process_message(message)

    async def on_message_edit(self, before: nextcord.Message, after: nextcord.Message):
        if after.author == self.user:
            return
        
        guild_config = await self.config_manager.get_guild_config(str(after.guild.id))
        if after.channel.id not in guild_config["allowed_channels"]:
            return

        # Convert message to universal format for cross-provider compatibility
        universal_message = {
            "role": "user", 
            "parts": [f"{after.author.display_name}: {after.content}"]
        }
        
        await guild_interaction_db.edit_guild_history(
            str(after.guild.id),
            universal_message,
            str(after.id)
        )

    async def on_message_delete(self, message: nextcord.Message):
        if message.guild is None:
            return
        
        await guild_interaction_db.remove_message_from_history(str(message.guild.id), str(message.id))

    async def process_message(self, message: nextcord.Message):
        guild_config = await self.config_manager.get_guild_config(str(message.guild.id))
        
        if message.channel.id not in guild_config["allowed_channels"]:
            return

        if guild_config["require_mention"] and self.user not in message.mentions:
            return

        # Get the selected provider
        provider_name = guild_config.get("ai_provider", "gemini")

        # Sync messages before processing
        await guild_interaction_db.sync_bot_user_messages(str(message.guild.id), message.channel.id, self)

        # Store message in universal format for cross-provider compatibility
        universal_message = {
            "role": "user", 
            "parts": [f"{message.author.display_name}: {message.content}"]
        }
        
        await guild_interaction_db.update_guild_history(
            str(message.guild.id),
            universal_message,
            str(message.id)
        )

        await self.generate_and_send_response(message, guild_config, provider_name)

    async def generate_and_send_response(self, message: nextcord.Message, guild_config: Dict[str, Any], provider_name: str):
        start_time = asyncio.get_event_loop().time()
        max_retry_time = 60  # 1 minute

        while asyncio.get_event_loop().time() - start_time < max_retry_time:
            try:
                # Get conversation history in universal format
                history = await guild_interaction_db.get_guild_history(str(message.guild.id))
                
                # Convert history to messages format
                messages = []
                for item in history:
                    messages.append({
                        "role": item["content"]["role"],
                        "parts": item["content"]["parts"]
                    })

                # Get API key
                api_key = await self.api_manager.get_api_key(str(message.guild.id))
                if not api_key:
                    await message.channel.send("No valid API key found for this guild. Please add an API key using the `/settings` command.")
                    return

                # Prepare config for the provider
                provider_config = guild_config.copy()
                provider_config["api_key"] = api_key
                
                # Add provider-specific settings
                provider_settings = guild_config.get("provider_settings", {}).get(provider_name, {})
                provider_config.update(provider_settings)
                
                # Only include safety_settings for Gemini
                if provider_name != "gemini" and "safety_settings" in provider_config:
                    del provider_config["safety_settings"]

                # Generate response
                response = await self.provider_manager.generate_response(
                    provider_name,
                    messages,
                    provider_config
                )
                
                response_parts = self.split_message(response)
                bot_messages = []
                
                for part in response_parts:
                    bot_message = await message.channel.send(part)
                    bot_messages.append(bot_message)
                
                # Store response in universal format
                full_response = {"role": "model", "parts": [response]}
                for bot_message in bot_messages:
                    await guild_interaction_db.update_guild_history(
                        str(message.guild.id), 
                        full_response, 
                        str(bot_message.id)
                    )
                
                return
            except Exception as e:
                await self.error_handler.log_error(e)
                error_result = await self.error_handler.handle_error(e, message.channel)
                if error_result is not None:
                    return
                await asyncio.sleep(5)

        await message.channel.send(embed=nextcord.Embed(
            title="Error", 
            description="I'm sorry, but I couldn't get a response after trying for a minute. Please try again later.", 
            color=nextcord.Color.red()
        ))

    @staticmethod
    def split_message(message: str, max_length: int = 2000) -> List[str]:
        if len(message) <= max_length:
            return [message]
        
        parts = []
        while len(message) > max_length:
            split_index = message.rfind(' ', 0, max_length)
            if split_index == -1:
                split_index = max_length
            parts.append(message[:split_index])
            message = message[split_index:].lstrip()
        
        if message:
            parts.append(message)
        
        return parts

async def main():
    client = AliciaBot()
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())