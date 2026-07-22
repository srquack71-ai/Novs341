"""Cog de comandos divertidos."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Fun")


class Fun(commands.Cog):
    """Comandos divertidos."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="dice")
    async def dice_command(self, ctx: commands.Context):
        """Rola um dado."""
        await ctx.send("Comandos divertidos em desenvolvimento.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Fun(bot))
    log.info("Cog Fun carregado")
