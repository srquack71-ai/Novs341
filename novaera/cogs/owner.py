"""Cog de comandos do dono do bot."""
from __future__ import annotations
import logging

import discord
from discord.ext import commands

from utils.checks import is_owner

log = logging.getLogger("NovaEra.Owner")


class Owner(commands.Cog):
    """Comandos exclusivos do dono."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync")
    @is_owner()
    async def sync_command(self, ctx: commands.Context):
        """Sincroniza comandos slash."""
        await ctx.send("Comandos sincronizados.")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Owner(bot))
    log.info("Cog Owner carregado")
