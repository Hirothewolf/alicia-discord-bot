import discord
import os
import asyncio
from dotenv import load_dotenv
from discord import app_commands
from typing import Dict, Any, Optional, List

from lib.alicia_presence_manager import AliciaPresenceManager
from lib.config_manager import ConfigManager
from lib.error_handler import ErrorHandler
from lib.gemini_model import GeminiModel
from lib import guild_interaction_db
from lib.api_manager import APIManager

from commands.settings_manager import setup_commands as setup_extra_commands
from commands.help_menu import setup_help_command
from commands.config_command import ConfigModal, SystemInstructionModal
from commands.safety_command import setup as setup_safety
from commands.channel_command import setup as setup_channel
from commands.import_instruction import setup as setup_import_instruction

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

class AliciaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.presence_manager: Optional[AliciaPresenceManager] = None
        self.dm_error_sent: Dict[int, bool] = {}
        self.sync_task = None

        # Initialize managers
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler()
        self.api_manager = APIManager(self.config_manager)
        self.gemini_model = GeminiModel(self.api_manager, self.config_manager, self.error_handler)
        self.guild_history_manager = guild_interaction_db

    async def setup_hook(self):
        # Load or create default config
        await self.config_manager.load_or_create_default_config()

        # Initialize GeminiModel
        await self.gemini_model.initialize()

        # Setup commands
        await setup_extra_commands(self.tree, self, self.config_manager, self.api_manager)
        await setup_help_command(self.tree)
        await setup_safety(self.tree)
        await setup_channel(self.tree)
        await setup_import_instruction(self.tree)

        # Initialize the AliciaPresenceManager
        self.presence_manager = AliciaPresenceManager(self)
        self.presence_manager.start()

        # Start periodic sync task
        self.sync_task = self.loop.create_task(self.periodic_sync())

        try:
            await self.tree.sync()
            print("Commands Synced!")
        except discord.errors.HTTPException as e:
            print(f"Error syncing commands: {e}")

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

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if isinstance(message.channel, discord.DMChannel):
            if message.author.id not in self.dm_error_sent:
                await message.channel.send("Sorry, Alicia is not available for use in direct messages")
                self.dm_error_sent[message.author.id] = True
            return

        await self.process_message(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author == self.user:
            return
        
        guild_config = await self.config_manager.get_guild_config(str(after.guild.id))
        if after.channel.id not in guild_config["allowed_channels"]:
            return

        await guild_interaction_db.edit_guild_history(
            str(after.guild.id),
            {"role": "user", "parts": [f"{after.author.display_name}: {after.content}"]},
            str(after.id)
        )

    async def on_message_delete(self, message: discord.Message):
        if message.guild is None:
            return
        
        await guild_interaction_db.remove_message_from_history(str(message.guild.id), str(message.id))

    async def process_message(self, message: discord.Message):
        guild_config = await self.config_manager.get_guild_config(str(message.guild.id))
        
        if message.channel.id not in guild_config["allowed_channels"]:
            return

        if guild_config["require_mention"] and self.user not in message.mentions:
            return

        # Sync messages before processing
        await guild_interaction_db.sync_bot_user_messages(str(message.guild.id), message.channel.id, self)

        await guild_interaction_db.update_guild_history(
            str(message.guild.id),
            {"role": "user", "parts": [f"{message.author.display_name}: {message.content}"]},
            str(message.id)
        )

        await self.generate_and_send_response(message, guild_config)

    async def generate_and_send_response(self, message: discord.Message, guild_config: Dict[str, Any]):
        start_time = asyncio.get_event_loop().time()
        max_retry_time = 60  # 1 minute

        while asyncio.get_event_loop().time() - start_time < max_retry_time:
            try:
                response = await self.gemini_model.generate_response(
                    message,
                    str(message.guild.id),
                    self.config_manager.get_guild_config,
                    guild_interaction_db.get_guild_history
                )
                
                response_parts = self.split_message(response)
                bot_messages = []
                
                for part in response_parts:
                    bot_message = await message.channel.send(part)
                    bot_messages.append(bot_message)
                
                full_response = {"role": "model", "parts": [response]}
                for bot_message in bot_messages:
                    await guild_interaction_db.update_guild_history(str(message.guild.id), full_response, str(bot_message.id))
                
                return
            except Exception as e:
                await self.error_handler.log_error(e)
                error_result = await self.error_handler.handle_error(e, message.channel)
                if error_result is not None:
                    return
                await asyncio.sleep(5)

        await message.channel.send(embed=discord.Embed(title="Error", description="I'm sorry, but I couldn't get a response after trying for a minute. Please try again later.", color=discord.Color.red()))

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