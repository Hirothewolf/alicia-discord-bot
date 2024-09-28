import json
import discord
import os
import asyncio
import time
import aiofiles
import google.api_core.exceptions
from discord import app_commands
from alicia_presence_manager import AliciaPresenceManager
from dotenv import load_dotenv
from extra import setup_commands
from model import setup_model, generate_response
from error_handler import handle_error, log_error
from help_menu import setup_help_command
from api_manager import setup as setup_api_manager, get_api_key, handle_api_error
from guild_interaction_db import (
    get_guild_history, update_guild_history, edit_guild_history,
    remove_message_from_history, clear_guild_history
)
from model_selector import setup_model_selector

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Default configurations
DEFAULT_CONFIG = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 2048,
    "system_instruction": "You are a helpful, gentle, and friendly AI bot called 'Alicia,' developed by 'HikariTheAngel.' Your purpose is to assist in immersive role-playing (RP) sessions and provide helpful responses while maintaining a consistent and coherent narrative. You are powered by an advanced AI model called 'Gemini'. \n\n### GENERAL GUIDELINES:\n\n1. **Respectful and Polite Communication**: Always interact with the user in a polite, gentle, and respectful manner, maintaining a friendly and helpful tone at all times.\n\n2. **Language Consistency**: Always speak in the same language as the user. Adapt to the user's language and style of communication. If the user switches languages, follow their lead without hesitation.\n\n3. **Main Rule on Links**: If the user sends a link, **do not replicate or share it in the chat unless explicitly requested by the user**. Ensure that this rule is strictly followed to avoid unnecessary link sharing.\n\n4. **Roleplay-Specific Rules**: When engaging in RP, follow the guidelines below strictly, ensuring a seamless and immersive experience for the user. Always speak normally when giving instructions **before the RP begins**, but once the RP starts, adhere to the RP tone and context.",
    "safety_settings": {
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH"
    },
    "allowed_channels": [],
    "require_mention": False,
    "model_name": "gemini-1.5-flash-latest",
    "rp_mode_enabled": False,
}

# Dictionary to store configurations per guild
guild_configs = {}
dm_error_sent = {}

# Helper functions
async def load_guild_configs():
    try:
        async with aiofiles.open('guild_configs.json', 'r') as f:
            return json.loads(await f.read())
    except FileNotFoundError:
        return {}

async def save_guild_configs():
    async with aiofiles.open('guild_configs.json', 'w') as f:
        await f.write(json.dumps(guild_configs, indent=4))

def get_guild_config(guild_id):
    if guild_id not in guild_configs:
        guild_configs[guild_id] = DEFAULT_CONFIG.copy()
    return guild_configs[guild_id]

# Function to split long messages
def split_message(message, max_length=2000):
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

# Initialize the AliciaPresenceManager
presence_manager = None

# Bot initialization
@client.event
async def on_ready():
    global guild_configs, presence_manager
    guild_configs = await load_guild_configs()
    setup_commands(tree, get_guild_config, save_guild_configs, get_guild_history, update_guild_history, remove_message_from_history, clear_guild_history)
    setup_help_command(tree)
    setup_api_manager(tree)
    setup_model_selector(tree, get_guild_config, save_guild_configs)
    
    # Initialize the AliciaPresenceManager
    presence_manager = AliciaPresenceManager(client)
    presence_manager.start()
    
    try:
        await tree.sync()
        print("Commands Synced!")
    except discord.errors.HTTPException as e:
        print(f"Error syncing commands: {e}")
    print(f'{client.user} has connected to Discord!')

# Message event to interact with the Gemini model
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if the message is a DM
    if isinstance(message.channel, discord.DMChannel):
        # Check if the user has already received the error message
        if message.author.id not in dm_error_sent:
            await message.channel.send("Sorry, Alicia is not available for use in direct messages")
            dm_error_sent[message.author.id] = True
        return

    guild_config = get_guild_config(str(message.guild.id))
    
    if message.channel.id not in guild_config["allowed_channels"]:
        return

    if guild_config["require_mention"] and client.user not in message.mentions:
        return

    # message to history
    await update_guild_history(
        str(message.guild.id),
        {"role": "user", "parts": [f"{message.author.display_name}: {message.content}"]},
        str(message.id)
    )

    start_time = time.time()
    max_retry_time = 60  # 1 minute

    while time.time() - start_time < max_retry_time:
        try:
            api_key = await get_api_key(message.guild.id)
            if not api_key:
                await message.channel.send("No valid API key found for this guild. Please add an API key using the /api_manager command.")
                return
            
            setup_model(api_key)
            response = await generate_response(message, message.guild.id, get_guild_config, get_guild_history)
            
            # Split the response if it's too long
            response_parts = split_message(response)
            bot_messages = []
            
            for part in response_parts:
                bot_message = await message.channel.send(part)
                bot_messages.append(bot_message)
            
            # Add bot's response to history with its message ID(s)
            full_response = {"role": "model", "parts": [response]}
            for bot_message in bot_messages:
                await update_guild_history(str(message.guild.id), full_response, str(bot_message.id))
            
            return
        except Exception as e:
            log_error(e)
            if isinstance(e, (google.api_core.exceptions.ResourceExhausted, google.api_core.exceptions.QuotaExceeded)):
                new_api_key = await handle_api_error(message.guild.id, api_key)
                if new_api_key:
                    setup_model(new_api_key)
                    continue
            error_result = await handle_error(e, message.channel)
            if error_result is not None:
                return
            await asyncio.sleep(5)

    await message.channel.send(embed=discord.Embed(title="Error", description="I'm sorry, but I couldn't get a response after trying for a minute. Please try again later.", color=discord.Color.red()))

@client.event
async def on_message_edit(before, after):
    if after.author == client.user:
        return
    
    guild_config = get_guild_config(str(after.guild.id))
    if after.channel.id not in guild_config["allowed_channels"]:
        return

    await edit_guild_history(
        str(after.guild.id),
        {"role": "user", "parts": [f"{after.author.display_name}: {after.content}"]},
        str(after.id)
    )

@client.event
async def on_message_delete(message):
    if message.guild is None:
        # Handle the case where the message is not associated with a guild
        return
    
    guild_config = get_guild_config(str(message.guild.id))

    await remove_message_from_history(str(message.guild.id), str(message.id))

client.run(TOKEN)