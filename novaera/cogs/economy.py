"""Cog de economia (moedas, banco, trabalho)."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Economy")


class Economy(commands.Cog):
    """Comandos de economia."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="balance")
    async def balance_command(self, ctx: commands.Context):
        """Mostra seu saldo."""
        await ctx.send("Comando de economia em desenvolvimento.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Economy(bot))
    log.info("Cog Economy carregado")
