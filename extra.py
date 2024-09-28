import discord
from discord import app_commands
from discord.ui import Button, View
from settings_commands import admin_only, setup_config_commands
import asyncio

def setup_commands(tree, get_guild_config, save_guild_configs, get_guild_history, update_guild_history, remove_message_from_history, clear_guild_history):
    # Set up configuration commands
    setup_config_commands(tree, get_guild_config, save_guild_configs, get_guild_history, update_guild_history)

    async def send_or_update_message(interaction, embed, view=None, ephemeral=True, delete_after=None):
        try:
            if interaction.response.is_done():
                if view:
                    message = await interaction.followup.send(embed=embed, view=view, ephemeral=ephemeral)
                else:
                    message = await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                if view:
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=ephemeral)
                    message = await interaction.original_response()
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
                    message = await interaction.original_response()
            
            if delete_after is not None and not ephemeral:
                await asyncio.sleep(delete_after)
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
        except discord.errors.NotFound:
            try:
                if view:
                    message = await interaction.followup.send(embed=embed, view=view, ephemeral=ephemeral)
                else:
                    message = await interaction.followup.send(embed=embed, ephemeral=ephemeral)
                
                if delete_after is not None and not ephemeral:
                    await asyncio.sleep(delete_after)
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass
            except discord.errors.HTTPException:
                pass

    class ExtraView(View):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(timeout=300)
            self.interaction = interaction

        @discord.ui.button(label="Clear History", style=discord.ButtonStyle.danger)
        async def clear_history(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            if button_interaction.user != self.interaction.user:
                embed = discord.Embed(title="Error", description="You cannot use this button.", color=discord.Color.red())
                await send_or_update_message(button_interaction, embed, delete_after=5)
                return
            
            guild_id = str(button_interaction.guild_id)
            history = await get_guild_history(guild_id)
            interaction_count = len(history)

            confirm_view = View()
            confirm_button = Button(label="Confirm", style=discord.ButtonStyle.danger)
            cancel_button = Button(label="Cancel", style=discord.ButtonStyle.secondary)

            async def confirm_callback(confirm_interaction: discord.Interaction):
                await clear_guild_history(guild_id)
                embed = discord.Embed(title="Chat History Cleared", description="All chat interactions have been removed from the bot's memory.", color=discord.Color.green())
                await send_or_update_message(confirm_interaction, embed, delete_after=5)

            async def cancel_callback(cancel_interaction: discord.Interaction):
                embed = discord.Embed(title="Operation Cancelled", description="Chat history clearing has been cancelled.", color=discord.Color.blue())
                await send_or_update_message(cancel_interaction, embed, delete_after=5)

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            embed = discord.Embed(
                title="Clear Chat History",
                description=f"Are you sure you want to clear all {interaction_count} chat interactions from the bot's memory?\n\n**This action cannot be undone.**",
                color=discord.Color.red()
            )

            await send_or_update_message(button_interaction, embed, view=confirm_view)

        @discord.ui.button(label="Toggle RP Mode", style=discord.ButtonStyle.primary)
        async def toggle_rp_mode(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            if button_interaction.user != self.interaction.user:
                embed = discord.Embed(title="Error", description="You cannot use this button.", color=discord.Color.red())
                await send_or_update_message(button_interaction, embed, delete_after=5)
                return

            guild_id = str(button_interaction.guild_id)
            guild_config = get_guild_config(guild_id)
            guild_config["rp_mode_enabled"] = not guild_config["rp_mode_enabled"]
            await save_guild_configs()
            status = "enabled" if guild_config["rp_mode_enabled"] else "disabled"

            embed = discord.Embed(
                title="Role Play Mode Updated",
                description=f"Role Play mode has been {status} for this server.",
                color=discord.Color.green()
            )
            await send_or_update_message(button_interaction, embed, delete_after=5)

        @discord.ui.button(label="Toggle Mentions", style=discord.ButtonStyle.primary)
        async def toggle_mentions(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            if button_interaction.user != self.interaction.user:
                embed = discord.Embed(title="Error", description="You cannot use this button.", color=discord.Color.red())
                await send_or_update_message(button_interaction, embed, delete_after=5)
                return

            config = get_guild_config(str(button_interaction.guild_id))
            config["require_mention"] = not config["require_mention"]
            await save_guild_configs()
            status = "required" if config["require_mention"] else "not required"

            embed = discord.Embed(
                title="Mention Requirement Updated",
                description=f"Mention is now {status} for the bot to respond",
                color=discord.Color.green()
            )
            await send_or_update_message(button_interaction, embed, delete_after=5)

    @tree.command(name="extra", description="Access additional bot settings and actions")
    @admin_only()
    async def extra(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Additional Bot Settings",
            description="Click the buttons below to access different settings and actions:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Clear History", value="Clear all chat interactions from bot memory", inline=False)
        embed.add_field(name="Toggle RP Mode", value="Enable or disable Role Play mode", inline=False)
        embed.add_field(name="Toggle Mentions", value="Toggle whether the bot requires a mention to respond", inline=False)

        view = ExtraView(interaction)
        await send_or_update_message(interaction, embed, view=view, ephemeral=True)