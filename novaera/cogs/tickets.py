"""Cog de sistema de tickets."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Tickets")


class Tickets(commands.Cog):
    """Comandos de tickets."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ticket")
    async def ticket_command(self, ctx: commands.Context):
        """Abre um ticket."""
        await ctx.send("Sistema de tickets em desenvolvimento.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Tickets(bot))
    log.info("Cog Tickets carregado")
