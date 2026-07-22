"""Cog de música."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Music")


class Music(commands.Cog):
    """Comandos de música."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="play")
    async def play_command(self, ctx: commands.Context):
        """Toca uma música."""
        await ctx.send("Sistema de música em desenvolvimento.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Music(bot))
    log.info("Cog Music carregado")
