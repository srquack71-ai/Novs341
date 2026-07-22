"""NovaEraBot — ponto de entrada."""
from __future__ import annotations
import asyncio
import os
import sys
import logging
import traceback
import discord
from discord.ext import commands

from config import config
from database.models import db
from utils.embeds import error as embed_error, success as embed_success

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("NovaEra")

# Cogs a carregar
INITIAL_COGS = [
    "cogs.utility",
    "cogs.moderation",
    "cogs.ai",
    "cogs.welcome",
    "cogs.automod",
    "cogs.economy",
    "cogs.levels",
    "cogs.tickets",
    "cogs.music",
    "cogs.fun",
    "cogs.logging",
    "cogs.owner",
    "cogs.settings",
]

intents = discord.Intents.all()


class NovaEraBot(commands.Bot):
    """Bot principal do NovaEra."""

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.prefix),
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            owner_id=config.owner_id or None,
        )
        self.db = db
        self.config = config
        self.start_time = discord.utils.utcnow()

    async def setup_hook(self):
        """Executado antes de conectar."""
        await self.db.connect()
        log.info("Banco de dados conectado em %s", config.db_path)
        
        for cog in INITIAL_COGS:
            try:
                await self.load_extension(cog)
                log.info("Cog carregado: %s", cog)
            except Exception as e:
                log.error("Falha ao carregar %s\n%s", cog, traceback.format_exc())

    async def on_ready(self):
        """Executado quando o bot se conecta."""
        if not hasattr(self, "_ready_logged"):
            log.info("Logado como %s (ID: %s)", self.user, self.user.id)
            log.info("Em %d servidores", len(self.guilds))
            self._ready_logged = True
        
        await self.change_presence(
            status=config.status_enum,
            activity=discord.Activity(
                type=config.activity_enum, name=config.activity
            ),
        )


async def _on_command_error(bot: NovaEraBot, ctx: commands.Context, err: Exception):
    """Handler global de erros."""
    if isinstance(err, commands.CommandNotFound):
        return
    
    if isinstance(err, commands.CommandOnCooldown):
        e = embed_error(
            "Em cooldown",
            f"Tente novamente em **{err.retry_after:.1f}s**.\n`{ctx.command}` está em cooldown.",
        )
        await ctx.send(embed=e, delete_after=10)
        return
    
    if isinstance(err, commands.MissingPermissions):
        perms = ", ".join(err.missing_permissions)
        await ctx.send(embed=embed_error("Sem permissão", f"Faltam: `{perms}`"), delete_after=10)
        return
    
    if isinstance(err, commands.BotMissingPermissions):
        perms = ", ".join(err.missing_permissions)
        await ctx.send(
            embed=embed_error("Sem permissão (bot)", f"Eu preciso: `{perms}`"),
            delete_after=10
        )
        return
    
    if isinstance(err, commands.MissingRequiredArgument):
        await ctx.send(
            embed=embed_error(
                "Argumento faltando",
                f"`{err.param.name}` é obrigatório.\nUse `{config.prefix}help {ctx.command}`"
            )
        )
        return
    
    if isinstance(err, commands.BadArgument):
        await ctx.send(embed=embed_error("Argumento inválido", str(err)), delete_after=10)
        return
    
    if isinstance(err, commands.NoPrivateMessage):
        await ctx.send(embed=embed_error("Apenas em servidores", "Este comando não funciona em DM."))
        return
    
    if isinstance(err, commands.NotOwner):
        await ctx.send(embed=embed_error("Apenas dono", "Comando restrito ao dono do bot."))
        return
    
    if isinstance(err, commands.CheckFailure):
        await ctx.send(
            embed=embed_error("Sem permissão", "Você não pode usar este comando."),
            delete_after=10
        )
        return
    
    log.error("Erro em %s: %s", ctx.command, err)
    await ctx.send(
        embed=embed_error("Erro inesperado", f"```{err}```"),
        delete_after=15
    )


def main():
    """Função principal."""
    if not config.token:
        raise SystemExit("DISCORD_TOKEN não definido. Configure o .env.")
    
    bot = NovaEraBot()
    
    @bot.event
    async def on_command_error(ctx: commands.Context, err: Exception):
        await _on_command_error(bot, ctx, err)
    
    try:
        bot.run(config.token, reconnect=True)
    except Exception as e:
        log.error(f"Falha ao iniciar o bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
