import nextcord
from nextcord import app_commands
from nextcord.ui import Button, View

class HelpPaginator(nextcord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=300)
        self.embeds = embeds
        self.current_page = 0

    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.gray)
    async def previous_button(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.gray)
    async def next_button(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

def create_help_embeds():
    embeds = []

    # Initial page
    initial_embed = nextcord.Embed(
        title="Hello! I'm Alicia, Your AI Assistant(v1.0.6 | Angel Guardian)",
        description="""
        Hi there! I'm Alicia, a friendly AI assistant created to help you with all sorts of tasks. I'm powered by advanced language models and I'm here to chat, answer questions, and assist you in any way I can.

        I can engage in conversations on a wide range of topics, help with problem-solving, and even get creative with storytelling or role-playing. My knowledge spans various fields, from science and technology to arts and culture.

        To interact with me, just type your messages in the allowed channels. If mention mode is on, you'll need to tag me to get my attention. Don't hesitate to ask me anything – I'm always eager to learn and help!

        Use the navigation buttons below to learn more about my features and how to use them. Let's explore together!
        """,
        color=nextcord.Color.purple()
    )
    embeds.append(initial_embed)

    # Clear History
    clear_history_embed = nextcord.Embed(
        title="Clear History",
        description="This feature allows administrators to erase my memory of past interactions in the server.",
        color=nextcord.Color.blue()
    )
    clear_history_embed.add_field(name="Usage", value="Use the `/settings` command and click the 'Clear History' button.", inline=False)
    clear_history_embed.add_field(name="Effect", value="Removes all stored chat interactions, giving me a fresh start.", inline=False)
    clear_history_embed.add_field(name="Note", value="This action cannot be undone, so use it carefully!", inline=False)
    embeds.append(clear_history_embed)

    # Toggle RP Mode
    rp_mode_embed = nextcord.Embed(
        title="Toggle RP Mode",
        description="This feature switches between my normal conversation mode and a more immersive role-playing mode.",
        color=nextcord.Color.blue()
    )
    rp_mode_embed.add_field(name="Usage", value="Use the `/settings` command and click the 'Toggle RP Mode' button.", inline=False)
    rp_mode_embed.add_field(name="Effect", value="When enabled, I'll adapt my responses to better suit role-playing scenarios, using more creative and descriptive language.", inline=False)
    rp_mode_embed.add_field(name="Note", value="This setting affects my behavior server-wide.", inline=False)
    embeds.append(rp_mode_embed)

    # Toggle Mentions
    mentions_embed = nextcord.Embed(
        title="Toggle Mentions",
        description="This feature controls whether I respond to all messages or only when mentioned.",
        color=nextcord.Color.blue()
    )
    mentions_embed.add_field(name="Usage", value="Use the `/settings` command and click the 'Toggle Mentions' button.", inline=False)
    mentions_embed.add_field(name="Effect", value="When enabled, I'll only respond to messages that mention me. When disabled, I'll respond to all messages in allowed channels.", inline=False)
    mentions_embed.add_field(name="Note", value="This can help reduce noise in busy channels.", inline=False)
    embeds.append(mentions_embed)

    # Filter Safety
    safety_embed = nextcord.Embed(
        title="Filter Safety",
        description="This feature allows fine-tuning of my content filtering settings.",
        color=nextcord.Color.blue()
    )
    safety_embed.add_field(name="Usage", value="Use the `/filter_safety` command to modify safety settings.", inline=False)
    safety_embed.add_field(name="Effect", value="Adjusts how strictly I filter potentially inappropriate content in various categories like sexually explicit content, hate speech, harassment, and dangerous activities.", inline=False)
    safety_embed.add_field(name="Note", value="Even with all filters disabled, some topics are still off-limits due to my core programming.", inline=False)
    embeds.append(safety_embed)

    # Manage Channels
    channels_embed = nextcord.Embed(
        title="Manage Allowed Channels",
        description="This feature controls which channels I can interact in.",
        color=nextcord.Color.blue()
    )
    channels_embed.add_field(name="Usage", value="Use the `/manage_allowed_channel` command to add or remove channels.", inline=False)
    channels_embed.add_field(name="Effect", value="I will only respond in channels that have been explicitly allowed.", inline=False)
    channels_embed.add_field(name="Note", value="This helps maintain order and prevents me from interfering in inappropriate channels.", inline=False)
    embeds.append(channels_embed)

    # Models
    models_embed = nextcord.Embed(
        title="Select a Model",
        description="This feature allows selection from a range of AI models that power my responses.",
        color=nextcord.Color.blue()
    )
    models_embed.add_field(name="Usage", value="Use the `/settings` command and click the 'Select Model' button to view and choose from available models.", inline=False)
    models_embed.add_field(name="Effect", value="Changing the underlying AI model can significantly impact my response quality, capabilities, and overall performance.", inline=False)
    models_embed.add_field(name="Note", value="Different models are better suited for different tasks. Experiment to find the one that works best for your needs.", inline=False)
    embeds.append(models_embed)

    # API Manager
    api_embed = nextcord.Embed(
        title="API Manager",
        description="This feature allows management of API keys and settings for my functionality.",
        color=nextcord.Color.blue()
    )
    api_embed.add_field(name="Usage", value="Use the `/settings` command and click the 'Manage API Keys' button to view and update API settings.", inline=False)
    api_embed.add_field(name="Effect", value="Allows updating and managing API keys necessary for my operation.", inline=False)
    api_embed.add_field(name="Note", value="Proper API configuration is crucial for my functionality. Make sure to keep your API keys secure!", inline=False)
    embeds.append(api_embed)

    # LLM Settings
    settings_embed = nextcord.Embed(
        title="LLM Settings",
        description="This feature allows fine-tuning of my language model parameters.",
        color=nextcord.Color.blue()
    )
    settings_embed.add_field(name="Usage", value="Use the `/settings` command and click the 'LLM Settings' button to adjust parameters.", inline=False)
    settings_embed.add_field(name="Parameters", value="""
    - Temperature: Controls the randomness of the responses. Lower values (0.0-0.5) make me more predictable and serious, while higher values (1.5-2.0) make me more creative and humorous.
    - Top P: Controls the diversity of the responses. Lower values (0.0-0.5) make me more focused and repetitive, while higher values (0.95-1.0) make me more varied and creative.
    - Top K: Limits the number of tokens I consider when generating a response. Lower values (1-10) make me more focused and less prone to errors, while higher values (40-100) allow me to generate more diverse and sometimes incorrect responses.
    - Max Output Tokens: Sets the maximum number of tokens in my responses. Lower values (100-500) make me more concise, while higher values (2048-4096) allow me to generate longer and more detailed responses.
    """, inline=False)
    settings_embed.add_field(name="Note", value="Adjusting these settings can significantly change my behavior. Use with caution!", inline=False)
    embeds.append(settings_embed)
    
    # Import Instruction
    instruction_embed = nextcord.Embed(
        title="Import Instruction",
        description="This feature allows you to import custom instructions for me to follow.",
        color=nextcord.Color.blue()
    )
    instruction_embed.add_field(name="Usage", value="Use the `/import_instructions` command to upload a custom instruction file like a 'W++ character/lorebook/scenario' or 'Character_card' with more than 4000 characters.(150000 characters max)", inline=False)
    instruction_embed.add_field(name="Format", value="The instruction file should be a JSON file containing the instruction string, e.g. `{'instruction': 'Follow a fantasy storyline'}`.", inline=False)
    instruction_embed.add_field(name="Effect", value="The custom instruction will be used as my default instruction for this server. Useful for roleplay or other instruction scenarios", inline=False)
    instruction_embed.add_field(name="Note", value="Please make sure to finalize the instruction file externally before importing it. Due to Discord limitations, future changes to the instruction file should be made outside of this feature.", inline=False)
    embeds.append(instruction_embed)

    return embeds

async def setup_help_command(tree):
    @tree.command(name="help", description="Display help information about Alicia")
    async def help_command(interaction: nextcord.Interaction):
        embeds = create_help_embeds()
        paginator = HelpPaginator(embeds)
        await interaction.response.send_message(embed=embeds[0], view=paginator, ephemeral=True)