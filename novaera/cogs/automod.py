"""Cog de auto-moderação."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.AutoMod")


class AutoMod(commands.Cog):
    """Auto-moderação."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitora mensagens para auto-mod."""
        if message.author.bot:
            return


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(AutoMod(bot))
    log.info("Cog AutoMod carregado")
