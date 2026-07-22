"""Cog de logging de eventos do servidor."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Logging")


class Logging(commands.Cog):
    """Logging de eventos."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Logging(bot))
    log.info("Cog Logging carregado")
