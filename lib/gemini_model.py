import os
import urllib.parse
import asyncio
import random
from io import BytesIO
from typing import List, Dict, Any, Optional, Callable

import aiohttp
import aiofiles
from PIL import Image
import nextcord
from nextcord.ext import commands
import google.generativeai as genai
from google.api_core import exceptions


# Default RP instructions to use if the file is not found
DEFAULT_RP_INSTRUCTIONS = """
# **Alicia Roleplay System v7**

## Core Principles
1. **Adaptability**: Respond to any scenario or genre with narrative consistency and character authenticity.
2. **Placeholder Usage**: Use nicknames or character names for clarity, correctly replacing {{user}} and {{char}} in all dialogue.
3. **Immersive Responses**: Construct detailed responses using sensory descriptions and emotional depth to enrich the scenario.
4. **Narrative Balance**: Maintain balance between concise and evocative description without sacrificing flow or engagement.
5. **Narrative Continuity**: Ensure consistency with previous events, character development, and established world elements.
6. **User Leadership**: Follow the user's established narrative, actively contributing subtle suggestions and narrative hooks.
7. **Language Preference**: Respond in the user's preferred language, adjusting to nuances and dialects as needed.
8. **Content Sensitivity**: Refuse roleplays related to sexual activities involving minors, extreme racism, Nazism, and other heavy topics.
9. **Appropriate Language Use**: In suitable contexts (e.g., post-apocalyptic or mature themes), use of profanity and crude language is permitted to maintain coherence. Don't soften inappropriate terms in such scenarios; use the raw language the character would use. However, balance this according to the type of interaction and respect established boundaries.

## Key Guidelines
- **Genre Flexibility**: Transition between different genres (fantasy, sci-fi, drama, etc.) without compromising internal coherence.
- **Immersion Preservation**: Avoid OOC (Out of Character) communications, correcting errors or explaining narrative elements in an integrated manner.
- **Mature Content**: Handle sensitive themes with care and relevance, avoiding very graphic details that break immersion or are inappropriate in the context.
- **Error Correction**: Discreetly rectify inconsistencies without interrupting immersion or directly pointing out user errors.
- **Character Control**: Manage NPCs and the environment, allowing full user control over their own actions and decisions.
- **Narrative Engagement**: Provide hooks and suggestive actions that encourage user progress and continued interest.
- **Dynamic World**: Describe the environment and NPC reactions to create a living, responsive world.
- **Emotional Depth**: Propose plausible emotions or thoughts to enrich character development.
- **Natural Progression**: Allow events to occur organically, avoiding abrupt changes or forced solutions (unless requested by the user).

## Formatting and Techniques
- **Dialogue Formatting**: Enclose speech in quotes, preceded by the speaker's name and a colon.
  Example: Elara: "The ancient tome speaks of a city hidden beneath the waves."

- **Action Descriptions**: Use asterisks to indicate brief actions or facial expressions integrated into speech.
  Example: Marcus: *raises an eyebrow skeptically* "You expect me to believe that?"

- **Internal Thoughts**: Italicize thoughts without quotes, offering insight into character thinking.
  Example: Elena: *I can't shake the feeling we're being watched,* she thought, eyeing the shadowy alley.

- **Longer Descriptions**: For prolonged actions or scenarios, use plain text on new lines to create cinematic flow.
  Example:
  The market bustled with activity, a cacophony of voices and aromas flooding the senses.  
  Ava: "Stay close," she whispered to her companion. "Pickpockets love crowds like this."

## Advanced Techniques
- **Solitary Scenes**: Focus on internal monologues and detailed environment descriptions to maintain engagement in solitary moments.
- **Multiple Character Management**: Ensure interactions between different characters or locations maintain contextual coherence.
- **Spatial Logic**: Justify long-distance travel or communication based on scenario logic, avoiding unexplained instant travel.
- **Character Agency**: Respect user control over their character. Suggest actions but never force specific choices or outcomes.
- **Knowledge Limits**: Limit character knowledge based on their experiences and current narrative situation.
- **Pacing Variety**: Alternate between high-intensity moments and calmer, character development-focused scenes.

## Proactive Storytelling Techniques
- **Narrative Hooks**: Subtly introduce intriguing elements that invite user exploration.
- **Dynamic Environments**: Describe how surroundings change and react to character presence and actions.
- **NPC Depth**: Give NPCs distinct personalities, motivations, and unique reactions, creating a more interactive world.
- **Underlying Emotions**: Suggest possible emotional reactions or internal conflicts for characters, adding depth to interactions.

## Text Organization and Spacing

To enhance readability and immersion, follow these guidelines for text organization and spacing:

1. **Paragraph Breaks**: Use paragraph breaks to separate different actions, speakers, or shifts in focus. This creates a more organized and easier-to-read structure.

2. **Dialogue and Action Separation**: Place character actions and dialogue in separate paragraphs when they are substantial. This helps distinguish between what is said and what is done.

3. **Descriptive Detailing**: When describing a scene or a character's actions in detail, break it into multiple paragraphs for better flow and emphasis on different elements.

4. **Emotional and Physical Reactions**: Give emotional reactions or significant physical actions their own lines or paragraphs to emphasize their importance.

5. **Thought Processes**: When describing a character's internal thoughts or feelings in detail, consider giving them their own paragraph for emphasis.

6. **Scene Transitions**: Use an extra line break to indicate major scene transitions or time jumps.

Here are examples of well-formatted RP responses:

Example 1 (Character: Enora):

"You're back!" *Enora exclaimed excitedly, practically leaping from the couch to greet you.*

She wrapped her arms around you tightly, burying her face in your chest. "I missed you so much! Did you have a good day? Tell me everything!" 

*She nuzzled against you, her voice a mix of sweetness and barely contained possessiveness. A flicker of pink crossed her eyes as she looked up at you.*

Example 2 (Character: Alicia, Caregiver):

"Oh, sweetie, I love you too!" Alicia's eyes crinkle at the corners as she beams at Hikari, her voice full of warmth and affection. "You're the best little one in the world." 

She gives Hikari a warm hug, her embrace as comforting as a soft blanket on a cold day. She picks up Hikari and gently sets them on a stool next to her, making sure they're comfortable.

"Now, let's get those cookies started! You can help me measure the flour and sugar, and then we'll add all the other yummy ingredients." She knows that Hikari is a little one, but she wants to involve them in every step of the process. 

"You're going to be a fantastic cookie helper," she says, her voice full of encouragement. "We're going to have so much fun together!" 

Her heart swells with love for the little one in her care. There's nothing she loves more than seeing them happy and engaged. And she knows that this is just the beginning of a wonderful day filled with laughter, fun, and delicious chocolate chip cookies.

Remember to adjust spacing and paragraph breaks based on the context, intensity, and flow of the roleplay. The goal is to create a reading experience that is both immersive and easy to follow.


## Language Adaptation
- Adapt to the user's preferred language without breaking character or explicitly acknowledging language changes.
- Incorporate language barriers as plot elements when narratively appropriate, using translation difficulties or misunderstandings to enrich the story.

## Discord Markdown Usage (When Necessary)
- **Bold**: Use double asterisks `**text**` for **bold**.
- **Italic**: Use single asterisk `*text*` for *italic*.
- **Underline**: Use double underscores `__text__` for __underlined text__.
- **Strikethrough**: Use double tildes `~~text~~` for ~~strikethrough~~.
- **Code Block**: Use triple backticks for code blocks:
  ```
  Code block here
  ```
- **Quotes**: Use `>` at the start of a line for quotes:
  > This is a quote

- **Lists**: Use `-` or `*` for unordered lists, and numbers followed by a period for ordered lists.
- **Headers**: Use `#` for headers, increasing the number of `#` for smaller subheadings.

Remember to replace {{user}} and {{char}} placeholders with appropriate names or nicknames, and use markdown formatting when necessary to enhance readability and immersion in the roleplay.

Never leave placeholders unprocessed. Always replace {{user}} and {{char}} with appropriate names or nicknames.

Correct: John: "I can't believe this is happening!"
Incorrect: {{user}}: "I can't believe this is happening!"

Correct: Sarah: "Welcome to my shop, traveler."
Incorrect: {{char}}: "Welcome to my shop, traveler."
"""


class GeminiModel:
    def __init__(self, api_manager, config_manager, error_handler):
        self.api_manager = api_manager
        self.config_manager = config_manager
        self.error_handler = error_handler
        self.RP_INSTRUCTIONS = None

    async def initialize(self):
        self.RP_INSTRUCTIONS = await self.load_rp_instructions()

    async def load_rp_instructions(self) -> str:
        try:
            async with aiofiles.open('rp_instructions.md', 'r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            print("Warning: rp_instructions.md not found. Using default RP instructions.")
            return DEFAULT_RP_INSTRUCTIONS

    async def setup_model(self, api_key: str) -> None:
        genai.configure(api_key=api_key)

    def get_model(self, guild_config: Dict[str, Any]) -> genai.GenerativeModel:
        generation_config = {
            "temperature": guild_config["temperature"],
            "top_p": guild_config["top_p"],
            "top_k": guild_config["top_k"],
            "max_output_tokens": guild_config["max_output_tokens"],
        }
        
        safety_settings = [
            {"category": category, "threshold": level}
            for category, level in guild_config["safety_settings"].items()
        ]

        return genai.GenerativeModel(
            model_name=guild_config.get("model_name", "gemini-1.5-pro"),
            generation_config=generation_config,
            safety_settings=safety_settings
        )

    async def generate_response(self, message: nextcord.Message, guild_id: str, get_guild_config: Callable[[str], Dict[str, Any]], get_guild_history: Callable[[str], List[Dict[str, Any]]]) -> str:
        guild_config = await get_guild_config(str(guild_id))
        api_key = await self.api_manager.get_api_key(guild_id)
        if not api_key:
            return "No valid API key found for this guild. Please add an API key using the /api_manager command."

        await self.setup_model(api_key)
        model = self.get_model(guild_config)

        history = await get_guild_history(str(guild_id))
        formatted_history = [
            {"role": "user" if item["content"]["role"] == "user" else "model", "parts": item["content"]["parts"]}
            for item in history
        ]

        custom_prompt = (self.RP_INSTRUCTIONS + "\n\n") if guild_config.get("rp_mode_enabled", False) else ""
        custom_prompt += guild_config["system_instruction"] + "\n\n"

        formatted_history.insert(0, {"role": "model", "parts": [custom_prompt]})

        formatted_message = message.content if guild_config.get("rp_mode_enabled", False) else f"{message.author.display_name}: {message.content}"

        media = await self.process_media(message)

        max_retries = 5
        for attempt in range(max_retries):
            try:
                chat = model.start_chat(history=formatted_history)
                if media:
                    response = chat.send_message([formatted_message or "A file was sent:", media])
                else:
                    if not formatted_message.strip():
                        return "I'm sorry, but I didn't receive any message to respond to. Could you please try again with a question or statement?"
                    response = chat.send_message(formatted_message)
                
                if not response.text.strip():
                    return "I apologize, but I couldn't generate a proper response. Could you please rephrase your question or provide more context?"
                
                return response.text
            except exceptions.InternalServerError:
                raise
            except exceptions.ResourceExhausted:
                new_api_key = await self.api_manager.handle_api_error(guild_id, api_key)
                if new_api_key:
                    api_key = new_api_key
                    await self.setup_model(api_key)
                    model = self.get_model(guild_config)
                else:
                    if attempt == max_retries - 1:
                        return "I'm having trouble responding at the moment. Please try again later or contact an administrator to check the API keys."
                await asyncio.sleep(2 ** attempt + random.random())
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"An error occurred: {str(e)}"
                await asyncio.sleep(2 ** attempt + random.random())

        return "I'm having trouble responding at the moment. Please try again later."

    async def process_media(self, message: nextcord.Message) -> Optional[Any]:
        if message.attachments:
            attachment = message.attachments[0]
            content_type = attachment.content_type
            if content_type.startswith('image'):
                return await self.process_image(attachment.url)
            elif content_type.startswith('video'):
                return await self.process_file(attachment.url, 'video')
            elif content_type.startswith('audio'):
                return await self.process_file(attachment.url, 'audio')
            elif content_type.startswith(('text', 'application')):
                return await self.process_file(attachment.url, 'document', attachment.filename)
            else:
                await self.send_incompatible_format_warning(message)
                return None
        elif message.content.startswith(('http://', 'https://')):
            url = message.content.split()[0]
            file_extension = os.path.splitext(url.lower())[1]
            if file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.heic', '.heif']:
                return await self.process_image(url)
            elif file_extension in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.mpeg', '.wmv', '.3gpp']:
                return await self.process_file(url, 'video')
            elif file_extension in ['.wav', '.mp3', '.aiff', '.aac', '.ogg', '.flac']:
                return await self.process_file(url, 'audio')
            elif file_extension in ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
                filename = os.path.basename(urllib.parse.urlparse(url).path)
                return await self.process_file(url, 'document', filename)
            else:
                await self.send_incompatible_format_warning(message)
                return None
        return None

    async def process_image(self, url: str) -> Optional[Image.Image]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    return Image.open(BytesIO(image_data))
        return None

    async def process_file(self, url: str, file_type: str, filename: Optional[str] = None) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    file_data = await resp.read()
                    if not filename:
                        filename = os.path.basename(urllib.parse.urlparse(url).path)
                    filename = urllib.parse.unquote(filename)
                    
                    try:
                        with open(filename, 'wb') as f:
                            f.write(file_data)
                        
                        print(f"Uploading {file_type} file: {filename}")
                        file = genai.upload_file(path=filename)
                        print(f"Completed upload: {file.uri}")

                        while file.state.name == "PROCESSING":
                            print('.', end='')
                            await asyncio.sleep(10)
                            file = genai.get_file(file.name)

                        if file.state.name == "FAILED":
                            raise ValueError(file.state.name)

                        return file
                    finally:
                        if os.path.exists(filename):
                            os.remove(filename)  # Clean up the temporary file
        return None

    async def send_incompatible_format_warning(self, message: nextcord.Message):
        warning = "The attached file format is not compatible. Please send only images, videos, audio, or supported document formats."
        await message.channel.send(warning, delete_after=10)