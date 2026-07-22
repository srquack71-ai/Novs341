"""Cog de configurações do servidor."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

log = logging.getLogger("NovaEra.Settings")


class Settings(commands.Cog):
    """Comandos de configuração."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def setprefix_command(self, ctx: commands.Context, prefix: str):
        """Altera o prefixo do servidor."""
        await ctx.send("Configurações em desenvolvimento.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Settings(bot))
    log.info("Cog Settings carregado")
