import google.generativeai as genai
from google.api_core import exceptions
import asyncio
import random
import aiohttp
from io import BytesIO
from PIL import Image
import time
from api_manager import get_api_key, handle_api_error

# Load the RP instructions
try:
    with open('rp_instructions.json', 'r') as f:
        RP_INSTRUCTIONS = f.read()
except FileNotFoundError:
    RP_INSTRUCTIONS = ''

def setup_model(api_key):
    genai.configure(api_key=api_key)

def get_model(guild_config):
    generation_config = {
        "temperature": guild_config["temperature"],
        "top_p": guild_config["top_p"],
        "top_k": guild_config["top_k"],
        "max_output_tokens": guild_config["max_output_tokens"],
    }
    
    safety_settings = [
        {
            "category": category,
            "threshold": level
        }
        for category, level in guild_config["safety_settings"].items()
    ]

    selected_model = guild_config.get("model_name", "gemini-1.5-pro-latest")

    return genai.GenerativeModel(
        model_name=selected_model,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

async def generate_response(message, guild_id, get_guild_config, get_guild_history):
    guild_config = get_guild_config(str(guild_id))
    api_key = await get_api_key(guild_id)
    if not api_key:
        return "No valid API key found for this guild. Please add an API key using the /api_manager command."

    setup_model(api_key)
    model = get_model(guild_config)

    # Convert history to the format expected by the model
    history = await get_guild_history(str(guild_id))
    formatted_history = [
        {"role": "user" if item["content"]["role"] == "user" else "model", "parts": item["content"]["parts"]}
        for item in history
    ]

    # Create a custom prompt that includes RP instructions and system instructions
    custom_prompt = ""
    if guild_config.get("rp_mode_enabled", False):
        custom_prompt += RP_INSTRUCTIONS + "\n\n"
    custom_prompt += guild_config["system_instruction"] + "\n\n"

    # Add the custom prompt to the beginning of the chat history
    formatted_history.insert(0, {"role": "model", "parts": [custom_prompt]})

    chat = model.start_chat(history=formatted_history)

    # Format the user's message (remove the nickname in RP mode)
    if guild_config.get("rp_mode_enabled", False):
        formatted_message = message.content
    else:
        nickname = message.author.display_name
        formatted_message = f"{nickname}: {message.content}"

    # Check for attachments or image/video links
    media = None
    if message.attachments:
        attachment = message.attachments[0]
        if attachment.content_type.startswith('image'):
            media = await process_image(attachment.url)
        elif attachment.content_type.startswith('video'):
            media = await process_video(attachment.url)
    elif message.content.startswith(('http://', 'https://')):
        if any(ext in message.content.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.heic', '.heif']):
            media = await process_image(message.content)
        elif any(ext in message.content.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.mpeg', '.wmv']):
            media = await process_video(message.content)

    max_retries = 5
    for attempt in range(max_retries):
        try:
            if media:
                if message.content.strip():
                    # If there's both text and media (image/video)
                    response = chat.send_message([formatted_message, media])
                else:
                    # If there's only media
                    response = chat.send_message([f"A file was sent:", media])
            else:
                # If there's only text
                response = chat.send_message(formatted_message)
            return response.text
        except exceptions.InternalServerError:
            # Re-raise the InternalServerError to be handled in the main.py
            raise
        except exceptions.ResourceExhausted:
            new_api_key = await handle_api_error(guild_id, api_key)
            if new_api_key:
                api_key = new_api_key
                setup_model(api_key)
                model = get_model(guild_config)
                chat = model.start_chat(history=formatted_history)
            else:
                if attempt == max_retries - 1:
                    return "I'm having trouble responding at the moment. Please try again later or contact an administrator to check the API keys."
            await asyncio.sleep(2 ** attempt + random.random())
        except Exception as e:
            if attempt == max_retries - 1:
                return f"An error occurred: {str(e)}"
            await asyncio.sleep(2 ** attempt + random.random())

    return "I'm having trouble responding at the moment. Please try again later."

async def process_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                image = Image.open(BytesIO(image_data))
                return image
    return None

async def process_video(url):
    # Upload video to the File API and handle the processing
    video_file_name = url.split("/")[-1]

    print(f"Uploading video file: {video_file_name}")
    
    video_file = genai.upload_file(path=video_file_name)
    print(f"Completed upload: {video_file.uri}")

    # Check the video state until it is ready (ACTIVE)
    while video_file.state.name == "PROCESSING":
        print('.', end='')
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(video_file.state.name)

    return video_file