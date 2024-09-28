import discord
from discord import app_commands
from discord.ui import Modal, TextInput, Select, View
from model_selector import get_models, ModelSelector
from discord import Interaction
import asyncio

def is_admin(user):
    return user.guild_permissions.administrator

def admin_only():
    async def predicate(interaction: discord.Interaction):
        if not is_admin(interaction.user):
            embed = discord.Embed(
                title="Permission Denied",
                description="Only administrators can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            
            return False
        return True
    return app_commands.check(predicate)

def setup_config_commands(tree, get_guild_config, save_guild_configs, get_guild_history, save_guild_histories):
    class ConfigModal(Modal, title="Configure Bot Settings"):
        temperature = TextInput(label="Temperature (0-2)", default="0.9", required=True)
        top_p = TextInput(label="Top P (0-1)", default="0.95", required=True)
        top_k = TextInput(label="Top K (0-100)", default="64", required=True)
        max_tokens = TextInput(label="Max Output Tokens (0-4096)", default="2048", required=True)
        system_instruction = TextInput(label="System Instruction", style=discord.TextStyle.paragraph, required=True)

        def __init__(self, config):
            super().__init__()
            self.temperature.default = str(config.get("temperature", 0.9))
            self.top_p.default = str(config.get("top_p", 0.95))
            self.top_k.default = str(config.get("top_k", 64))
            self.max_tokens.default = str(config.get("max_output_tokens", 4096))
            self.system_instruction.default = config.get("system_instruction", "")

        async def on_submit(self, interaction: discord.Interaction):
            config = get_guild_config(str(interaction.guild_id))
            errors = []
            
            try:
                temp = float(self.temperature.value)
                if not 0 <= temp <= 2:
                    errors.append("Temperature must be between 0 and 2")
                else:
                    config["temperature"] = temp
            except ValueError:
                errors.append("Temperature must be a number")

            try:
                top_p = float(self.top_p.value)
                if not 0 <= top_p <= 1:
                    errors.append("Top P must be between 0 and 1")
                else:
                    config["top_p"] = top_p
            except ValueError:
                errors.append("Top P must be a number")

            try:
                top_k = int(self.top_k.value)
                if not 0 <= top_k <= 100:
                    errors.append("Top K must be between 0 and 100")
                else:
                    config["top_k"] = top_k
            except ValueError:
                errors.append("Top K must be an integer")

            try:
                max_tokens = int(self.max_tokens.value)
                if not 0 <= max_tokens <= 4096:
                    errors.append("Max Output Tokens must be between 0 and 4096")
                else:
                    config["max_output_tokens"] = max_tokens
            except ValueError:
                errors.append("Max Output Tokens must be an integer")

            config["system_instruction"] = self.system_instruction.value

            if errors:
                error_message = "\n".join(errors)
                embed = discord.Embed(
                    title="Configuration Error",
                    description=error_message,
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        
                await asyncio.sleep(10)
                await interaction.delete_original_response()
            else:
                await save_guild_configs()
                embed = discord.Embed(
                    title="Configuration Updated",
                    description="Configuration updated successfully!",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        
                await asyncio.sleep(10)
                await interaction.delete_original_response()

    @tree.command(name="settings", description="Configure LLM settings")
    @admin_only()
    async def configure(interaction: discord.Interaction):
        config = get_guild_config(str(interaction.guild_id))
        modal = ConfigModal(config)
        await interaction.response.send_modal(modal)

    @tree.command(name="filter_safety", description="Set the safety settings for the model")
    @admin_only()
    @app_commands.describe(
        category="Safety category to configure",
        level="Safety level to set"
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="Sexually Explicit", value="HARM_CATEGORY_SEXUALLY_EXPLICIT"),
            app_commands.Choice(name="Hate Speech", value="HARM_CATEGORY_HATE_SPEECH"),
            app_commands.Choice(name="Harassment", value="HARM_CATEGORY_HARASSMENT"),
            app_commands.Choice(name="Dangerous Content", value="HARM_CATEGORY_DANGEROUS_CONTENT")
        ],
        level=[
            app_commands.Choice(name="No Filter", value="BLOCK_NONE"),
            app_commands.Choice(name="Low Detection", value="BLOCK_ONLY_HIGH"),
            app_commands.Choice(name="Normal Detection", value="BLOCK_MEDIUM_AND_ABOVE"),
            app_commands.Choice(name="High Detection", value="BLOCK_LOW_AND_ABOVE")
        ]
    )
    async def set_safety(interaction: discord.Interaction, category: app_commands.Choice[str], level: app_commands.Choice[str]):
        config = get_guild_config(str(interaction.guild_id))
        config["safety_settings"][category.value] = level.value
        await save_guild_configs()
        embed = discord.Embed(
            title="Safety Setting Updated",
            description=f"Safety setting for {category.name} set to {level.name}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    class ChannelSelect(Select):
        def __init__(self, channels, action):
            options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]
            super().__init__(placeholder="Select a channel...", min_values=1, max_values=1, options=options)
            self.action = action

        async def callback(self, interaction: Interaction):
            channel_id = int(self.values[0])
            config = get_guild_config(str(interaction.guild_id))

            if self.action == "add":
                if channel_id not in config["allowed_channels"]:
                    config["allowed_channels"].append(channel_id)
                    await save_guild_configs()
                    embed = discord.Embed(title="Channel Added", description=f"Added <#{channel_id}> to allowed channels", color=discord.Color.green())
                else:
                    embed = discord.Embed(title="Channel Already Allowed", description=f"<#{channel_id}> is already an allowed channel", color=discord.Color.yellow())
            else:  # remove
                if channel_id in config["allowed_channels"]:
                    config["allowed_channels"].remove(channel_id)
                    await save_guild_configs()
                    embed = discord.Embed(title="Channel Removed", description=f"Removed <#{channel_id}> from allowed channels", color=discord.Color.green())
                else:
                    embed = discord.Embed(title="Channel Not in List", description=f"<#{channel_id}> is not in the allowed channels list", color=discord.Color.yellow())

            await interaction.response.edit_message(embed=embed, view=None)
            await asyncio.sleep(10)
            await interaction.delete_original_response()

    class ChannelSelectView(View):
        def __init__(self, channels, action):
            super().__init__()
            self.add_item(ChannelSelect(channels, action))

    @tree.command(name="manage_allowed_channel", description="Add or remove allowed channels")
    @admin_only()
    @app_commands.describe(
        action="Add or remove a channel",
        channel_name="Start typing to search for a channel"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add Channel", value="add"),
        app_commands.Choice(name="Remove Channel", value="remove")
    ])
    async def manage_allowed_channel(
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        channel_name: str
    ):
        matching_channels = [
            channel for channel in interaction.guild.channels
            if channel_name.lower() in channel.name.lower() and isinstance(channel, discord.TextChannel)
        ]

        if not matching_channels:
            embed = discord.Embed(
                title="No Channels Found",
                description=f"No channels matching '{channel_name}' were found.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        view = ChannelSelectView(matching_channels, action.value)
        embed = discord.Embed(
            title=f"Select Channel to {action.name}",
            description="Choose a channel from the dropdown menu:",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

