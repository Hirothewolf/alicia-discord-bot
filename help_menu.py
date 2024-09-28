import discord
from discord import app_commands
from discord.ui import Button, View

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Clear History", style=discord.ButtonStyle.primary)
    async def clear_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Clear History",
            description="This function allows administrators to clear the bot's chat history for the server.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/extra` command and click the 'Clear History' button.", inline=False)
        embed.add_field(name="Effect", value="Removes all stored chat interactions, giving the bot a fresh start.", inline=False)
        embed.add_field(name="Note", value="**This action cannot be undone. Use with caution.**\n\nThis feature is useful if you want to start from scratch or if the bot has been behaving erratically.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Toggle RP Mode", style=discord.ButtonStyle.primary)
    async def toggle_rp_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Toggle RP Mode",
            description="""
            This function allows administrators to enable or disable Role Play mode for the bot.

            When enabled, the bot will adapt its responses to better suit role-playing scenarios. This means that the bot will generate more
            creative and descriptive responses, taking into account the context of the conversation and the characters involved.

            RP Mode is useful for creating immersive role-playing experiences, where the bot will respond in a way that is more fitting for the
            scenario. For example, if the bot is in a fantasy setting, it may respond with more fantastical language and descriptions.
            """,
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/extra` command and click the 'Toggle RP Mode' button.", inline=False)
        embed.add_field(name="Effect", value="Enables or disables Role Play mode for the bot.", inline=False)
        embed.add_field(name="Note", value="Note that this setting affects the bot's behavior server-wide, so all channels will be affected by this setting.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Toggle Mentions", style=discord.ButtonStyle.primary)
    async def toggle_mentions(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Toggle Mentions",
            description="This function allows administrators to change whether the bot requires being mentioned to respond.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/extra` command and click the 'Toggle Mentions' button.", inline=False)
        embed.add_field(name="Effect", value="When enabled, the bot will only respond to messages that mention it. When disabled, it responds to all messages in allowed channels.", inline=False)
        embed.add_field(name="Note", value="This can help reduce noise in busy channels.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Filter Safety", style=discord.ButtonStyle.primary)
    async def filter_safety(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Filter Safety",
            description="""
            This function allows administrators to fine-tune the bot's content filtering settings to control the level of potentially inappropriate content allowed in the server. 
            
            The bot is capable of detecting and blocking content that might be harmful or offensive, and this feature allows you to adjust the strictness of this filtering. 
            
            **Even with all the filters disabled, some topics or interactions cannot be discussed by the bot due to internal limitations of the LLM.**         
            """,
            color=discord.Color.blue()
        )
        embed.add_field(name="Warning", value="""
            By disabling or reducing the safety filters, you may be exposed to content that is inappropriate, harmful, or offensive. 
            You are responsible for your own actions and the use of this bot. If your account is suspended due to inappropriate content, it is not the responsibility of the developers of Alicia or any affiliated parties. 
            
            **You have been warned.**""", inline=False)
        embed.add_field(name="Usage", value="Use the `/filter_safety` command to modify safety settings.", inline=False)
        embed.add_field(name="Effect", value="""
            Adjusts how strictly the bot filters potentially inappropriate content. The categories are:
            
            - **Sexually explicit**: content that is explicit, graphic, or contains sexual themes.
            - **Hate speech**: content that promotes or glorifies violence, discrimination, or hate against any individual or group based on race, ethnicity, national origin, religion, gender, sexual orientation, or disability.
            - **Harassment**: content that is intended to bully, intimidate, or humiliate.
            - **Promotes dangerous activities**: content that promotes or encourages dangerous or harmful activities.
            """, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Manage Channels", style=discord.ButtonStyle.primary)
    async def manage_allowed_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Manage Allowed Channels",
            description="This function allows administrators to control which channels the bot can interact in.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/config allowed_channels` command to add or remove channels.", inline=False)
        embed.add_field(name="Effect", value="The bot will only respond in channels that have been explicitly allowed.", inline=False)
        embed.add_field(name="Note", value="This helps maintain order and prevents the bot from interfering in inappropriate channels.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Models", style=discord.ButtonStyle.primary)
    async def models(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Select a Model",
            description="This function allows administrators to browse and select from a range of AI models, each with its own strengths and weaknesses.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/models` command to view available models and select one to use for the bot.", inline=False)
        embed.add_field(name="Effect", value="Changing the underlying AI model can significantly impact the bot's response quality, capabilities, and overall performance.", inline=False)
        embed.add_field(name="Note", value="Different models are better suited for different tasks and use cases. Experiment with different models to find the one that works best for you.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="API Manager", style=discord.ButtonStyle.primary)
    async def api_manager(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="API Manager",
            description="""
            This function allows administrators to manage API keys and settings for the bot.
            To use this feature, you will need to obtain an API key from the Google Gemini LLM service.
            
            **How to obtain an API key from the Google Gemini LLM service:**
            
            1. Go to the Login to your Google account, You should see the sign in button on the top right corner of Google’s home page.
            
            2. Visit the "[Google AI Studio](https://ai.google.dev/)".You'd then need to click on the “Gemini API” tab or click on the “Learn more about the Gemini API” button. Alternatively, you can visit the Gemini API landing page directly.
            
            3. Click on “Get API key in Google AI Studio”, This should appear as a button on the center of the page.
            
            4. Review and approve the terms of service.You should then see a pop-up that asks you to consent to Google APIs Terms of Service and Gemini API Additional Terms of Service. 
            
            While not required, you can also opt in to receive emails that keep you up to date on Google AI and ask you to participate in specific research studies for Google AI.
            
            5. Create your API key. You’ll then have the option to create an API key in a new project or via an existing project. Once you’ve chosen one of these options, your API key should be auto-generated! 
            """,
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/apimanager` command to view and update API settings.", inline=False)
        embed.add_field(name="Effect", value="Allows updating and managing API keys", inline=False)
        embed.add_field(name="Note", value="Proper API configuration is crucial for the bot's functionality.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    @discord.ui.button(label="Settings", style=discord.ButtonStyle.primary)
    async def llm_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Settings",
            description="""
            This function allows administrators to fine-tune the bot's language model settings to control the quality and style of responses.

            **Temperature:** Adjusts the randomness of the bot's responses. Lower values result in more conservative responses, while higher values increase the likelihood of more unusual responses. Think of it like a thermostat, where lower values result in more predictable responses and higher values result in more creative responses.

            **Top P:** Controls the cumulative probability of token selection for each response. Lower values limit the token pool to the most likely options, producing more focused, concise responses. Higher values allow a wider range of tokens, increasing the potential for longer, more detailed responses.

            **Top K:** Limits the number of tokens considered for each response. Lower values restrict the pool to only the most probable tokens, leading to shorter, more direct responses. Higher values expand the token pool, allowing for more diverse and extended outputs.

            **Max Output Tokens:** Adjusts the maximum number of tokens the bot will generate for a response. Think of it like a limit, where lower values result in shorter responses and higher values result in longer responses. For all Gemini models, a token is equivalent to about 4 characters.

            **System Instructions:** Allows adding custom instructions to the bot's responses, which can be used to tailor the bot's behavior to specific use cases. Think of it like a manual, where you can add specific instructions to the bot to help it understand what you want it to do.
            """,
            color=discord.Color.blue()
        )
        embed.add_field(name="Usage", value="Use the `/Settings` command to view and Edit LLM settings.", inline=False)
        embed.add_field(name="Effect", value="These settings affect the creativity, coherence, and length of the bot's responses. Think of it like a recipe, where the right combination of settings results in a response that is both creative and coherent.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
def setup_help_command(tree):
    @tree.command(name="help", description="Display help information about the bot")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Hey there, {interaction.user.name}! I'm Alicia",
            description="""
            I'm so glad you're here! I'm Alicia(Version 1.0 RC), a highly advanced AI designed to assist and chat with you. Developed By [Hirothewolf(aka. HikariTheAngel)](https://github.com/Hirothewolf) I can do all sorts of things, from answering questions to generating code. I'm like your personal assistant, but way more fun!

            Below, you'll find a list of all the things I can do. Just click on a button to learn more about each feature.
            """,
            color=discord.Color.green()
        )
        embed.add_field(name="**Clear History**", value="Erase the bot's memory of past interactions. This is useful if you want to start fresh or if you've shared something sensitive.", inline=True)
        embed.add_field(name="**Toggle RP Mode**", value="Switch between normal and role-play modes. In role-play mode, I'll respond in character, using my vast knowledge of stories and scenarios to create a more immersive experience.", inline=True)
        embed.add_field(name="**Toggle Mentions**", value="Change whether the bot needs to be mentioned. If you want me to respond to messages that don't mention me, toggle this off!", inline=True)
        embed.add_field(name="**Filter Safety**", value="Adjust content filtering settings. I'm designed to be safe and respectful, but you can adjust the filters to suit your needs.", inline=True)
        embed.add_field(name="**Manage Channels**", value="Control where the bot can interact. You can limit my interactions to specific channels or turn them off entirely.", inline=True)
        embed.add_field(name="**Models**", value="Select different AI models for the bot. I come with a range of models, each with its own strengths and weaknesses. You can choose the one that best fits your needs.", inline=True)
        embed.add_field(name="**API Manager**", value="Manage API keys and settings. If you want to use me with other services or integrations, you'll need to manage your API keys here.", inline=True)
        embed.add_field(name="**Settings**", value="Fine-tune language model parameters. If you're feeling adventurous, you can adjust the settings for my language model. Just be careful, as this can affect my performance!", inline=True)

        embed.set_footer(text="Thanks for chatting with me! I'm always here to help.")
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
