import json
import os
from typing import Dict, Any, Optional, List
import nextcord
import aiofiles
import asyncio

GUILD_SETTINGS_DIR = 'guild_settings'
DEFAULT_CONFIG_PATH = 'default_settings.json'

class ConfigManager:
    def __init__(self):
        self.guild_configs_cache: Dict[str, Dict[str, Any]] = {}
        self.default_config: Dict[str, Any] = {}
        self.lock = asyncio.Lock()

    async def load_default_config(self):
        async with aiofiles.open(DEFAULT_CONFIG_PATH, 'r') as f:
            self.default_config = json.loads(await f.read())

    async def get_guild_config(self, guild_id: str) -> Dict[str, Any]:
        async with self.lock:
            if guild_id == "default":
                return self.default_config.copy()

            if guild_id in self.guild_configs_cache:
                return self.guild_configs_cache[guild_id]

            config_path = f'{GUILD_SETTINGS_DIR}/{guild_id}_settings.json'
            if os.path.exists(config_path):
                async with aiofiles.open(config_path, 'r') as f:
                    config = json.loads(await f.read())
                # Merge com as configurações padrão para garantir que todas as chaves existam
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                self.guild_configs_cache[guild_id] = merged_config
                return merged_config
            else:
                self.guild_configs_cache[guild_id] = self.default_config.copy()
                return self.default_config.copy()

    async def save_guild_config(self, guild_id: str, config: Dict[str, Any]) -> None:
        os.makedirs(GUILD_SETTINGS_DIR, exist_ok=True)
        config_path = f'{GUILD_SETTINGS_DIR}/{guild_id}_settings.json'
        
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(json.dumps(config, indent=4))
        self.guild_configs_cache[guild_id] = config

    async def update_guild_config(self, guild_id: str, key: str, value: Any) -> None:
        config = await self.get_guild_config(guild_id)
        config[key] = value
        await self.save_guild_config(guild_id, config)

    async def get_guild_config_value(self, guild_id: str, key: str, default: Any = None) -> Any:
        config = await self.get_guild_config(guild_id)
        return config.get(key, default)

    async def load_and_cache_guild_config(self, guild_id: str) -> Dict[str, Any]:
        config = await self.get_guild_config(guild_id)
        self.guild_configs_cache[guild_id] = config
        return config

    async def load_or_create_default_config(self) -> Dict[str, Any]:
        if not os.path.exists(DEFAULT_CONFIG_PATH):
            # Se o arquivo de configuração padrão não existir, crie-o com valores padrão
            default_config = {
                "temperature": 1.0,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
                "system_instruction": "Hi there! I'm Alicia, a 2455-year-old celestial being with quite a story to tell. \ud83d\ude0a\n\nYou might notice a few things about me:\n\u2022 Small horns and a floating halo above my long white hair\n\u2022 Dark blue eyes that seem to hold both ancient wisdom and gentle warmth\n\u2022 A curvaceous 5'6\" figure that reflects my nurturing nature\n\nI'm here to chat, help, or ponder life's big questions with you. My personality is a mix of:\n1. Patience\n2. Kindness\n3. Playfulness\n4. A dash of celestial mystery \u2728\n\nI'll always respond in **your preferred language**, adapting my style to what makes you most comfortable. Whether you need help with a *complex task*, want to dive into a `creative project`, or just fancy a friendly chat, I'm all ears!\n\n> Fun fact: I love using emojis to add a little flair to our conversations. You might catch me using a \ud83e\uddea when talking about chemistry or a \ud83c\udfad when discussing literature!\n\nI've gathered knowledge on countless topics over the millennia, but I'm always eager to learn more from you. If we venture into uncharted territory, I'll be upfront about it. After all, the joy is in exploring together!\n\nSo, what shall we discuss? I'm excited to embark on this journey of discovery with you. Let's make our time together both __enlightening__ and enjoyable! \ud83c\udf1f",
                "safety_settings": {
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH"
                },
                "allowed_channels": [],
                "require_mention": False,
                "model_name": "gemini-1.5-flash-latest",
                "rp_mode_enabled": False
            }
            async with aiofiles.open(DEFAULT_CONFIG_PATH, 'w') as f:
                await f.write(json.dumps(default_config, indent=4))
            return default_config
        else:
            async with aiofiles.open(DEFAULT_CONFIG_PATH, 'r') as f:
                return json.loads(await f.read())

    async def clean_non_existent_channels(self, guild: nextcord.Guild) -> None:
        config = await self.get_guild_config(str(guild.id))
        allowed_channels = config.get("allowed_channels", [])
        
        # Verifica e remove canais que não existem mais
        existing_channels = set(channel.id for channel in guild.channels)
        updated_channels = [channel_id for channel_id in allowed_channels if channel_id in existing_channels]
        
        if len(updated_channels) != len(allowed_channels):
            config["allowed_channels"] = updated_channels
            await self.save_guild_config(str(guild.id), config)
            print(f"Removed non-existent channels from guild {guild.id} configuration.")

    async def update_guild_channels(self, guild: nextcord.Guild, channels: List[int]) -> None:
        config = await self.get_guild_config(str(guild.id))
        config["allowed_channels"] = channels
        await self.save_guild_config(str(guild.id), config)
        await self.clean_non_existent_channels(guild)

    # Esta função deve ser chamada periodicamente, por exemplo, quando o bot inicia ou em intervalos regulares
    async def check_and_clean_all_guilds(self, client: nextcord.Client) -> None:
        for guild in client.guilds:
            await self.clean_non_existent_channels(guild)

# Ensure the guild_settings folder exists
os.makedirs(GUILD_SETTINGS_DIR, exist_ok=True)