import nextcord
from nextcord import slash_command
from nextcord.ui import View, Select
from typing import List, Dict, Any

class ProviderSelect(Select):
    def __init__(self, providers: List[Dict[str, str]], config_manager, guild_id: str):
        self.config_manager = config_manager
        self.guild_id = guild_id
        
        options = [
            nextcord.SelectOption(
                label=provider["name"],
                value=provider["id"],
                description=provider["description"][:100]
            )
            for provider in providers
        ]
        
        super().__init__(
            placeholder="Select an AI Provider",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: nextcord.Interaction):
        await self.config_manager.update_guild_config(
            self.guild_id,
            "ai_provider",
            self.values[0]
        )
        
        embed = nextcord.Embed(
            title="AI Provider Updated",
            description=f"Successfully switched to {self.values[0]}",
            color=nextcord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ProviderView(View):
    def __init__(self, providers: List[Dict[str, str]], config_manager, guild_id: str):
        super().__init__()
        self.add_item(ProviderSelect(providers, config_manager, guild_id))

async def setup(bot):
    @bot.slash_command(
        name="select_provider",
        description="Select which AI provider to use"
    )
    async def select_provider(interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You need administrator permissions to use this command.",
                ephemeral=True
            )
            return

        providers = bot.provider_manager.get_available_providers()
        view = ProviderView(providers, bot.config_manager, str(interaction.guild_id))
        
        embed = nextcord.Embed(
            title="Select AI Provider",
            description="Choose which AI provider you want to use:",
            color=nextcord.Color.blue()
        )
        
        for provider in providers:
            embed.add_field(
                name=provider["name"],
                value=provider["description"],
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)