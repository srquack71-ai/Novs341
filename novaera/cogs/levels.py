"""Cog de níveis e XP."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Levels")


class Levels(commands.Cog):
    """Comandos de níveis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="level")
    async def level_command(self, ctx: commands.Context):
        """Mostra seu nível."""
        await ctx.send("Comando de níveis em desenvolvimento.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Levels(bot))
    log.info("Cog Levels carregado")
