import nextcord
from nextcord import Embed
from typing import List, Dict, Any
from lib.config_manager import ConfigManager
from lib.gemini_model import GeminiModel
from lib.guild_interaction_db import GuildHistoryManager
from lib.api_manager import APIManager
from lib.error_handler import ErrorHandler

class InteractionHandler:
    def __init__(self, client: nextcord.Client, config_manager: ConfigManager, 
                 model_manager: GeminiModel, guild_history_manager: GuildHistoryManager, 
                 api_manager: APIManager, error_handler: ErrorHandler):
        self.client = client
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.guild_history_manager = guild_history_manager
        self.api_manager = api_manager
        self.error_handler = error_handler

    async def handle_message(self, message: nextcord.Message) -> None:
        if message.author == self.client.user:
            return

        if isinstance(message.channel, nextcord.DMChannel):
            await self.handle_dm(message)
            return

        guild_config = await self.config_manager.get_guild_config(str(message.guild.id))
        if not await self.is_channel_allowed(message, guild_config):
            return

        await self.process_message(message, guild_config)

    async def handle_message_edit(self, before: nextcord.Message, after: nextcord.Message) -> None:
        if after.author == self.client.user:
            return
        
        guild_config = await self.config_manager.get_guild_config(str(after.guild.id))
        if not await self.is_channel_allowed(after, guild_config):
            return

        await self.guild_history_manager.edit_guild_history(
            str(after.guild.id),
            {"role": "user", "parts": [f"{after.author.display_name}: {after.content}"]},
            str(after.id)
        )

    async def handle_message_delete(self, message: nextcord.Message) -> None:
        if message.guild is None:
            return
        
        await self.guild_history_manager.remove_message_from_history(str(message.guild.id), str(message.id))

    async def handle_dm(self, message: nextcord.Message) -> None:
        embed = Embed(
            title="Direct Message Not Supported",
            description="Sorry, I'm not available for use in direct messages. Please use me in a server channel.",
            color=nextcord.Color.yellow()
        )
        await message.channel.send(embed=embed)

    async def is_channel_allowed(self, message: nextcord.Message, guild_config: Dict[str, Any]) -> bool:
        return (
            message.channel.id in guild_config.get("allowed_channels", []) and
            (not guild_config.get("require_mention", False) or self.client.user in message.mentions)
        )

    async def process_message(self, message: nextcord.Message, guild_config: Dict[str, Any]) -> None:
        await self.guild_history_manager.update_guild_history(
            str(message.guild.id),
            {"role": "user", "parts": [f"{message.author.display_name}: {message.content}"]},
            str(message.id)
        )

        try:
            response = await self.model_manager.generate_response(
                message, 
                str(message.guild.id), 
                self.config_manager.get_guild_config, 
                self.guild_history_manager.get_guild_history
            )
            await self.send_response(message, response)
        except Exception as e:
            await self.error_handler.handle_and_log_error(e, message.channel)

    async def send_response(self, message: nextcord.Message, response: str) -> None:
        response_parts = self.split_message(response)
        bot_messages = []
        
        for part in response_parts:
            bot_message = await message.channel.send(part)
            bot_messages.append(bot_message)
        
        full_response = {"role": "model", "parts": [response]}
        for bot_message in bot_messages:
            await self.guild_history_manager.update_guild_history(
                str(message.guild.id), 
                full_response, 
                str(bot_message.id)
            )

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