"""Cog de utilidade com comandos help, userinfo, etc."""
from __future__ import annotations
import logging
from collections import defaultdict
from typing import Optional

import discord
from discord.ext import commands

from config import config
from utils.embeds import info as embed_info, success as embed_success

log = logging.getLogger("NovaEra.Utility")

# Importar o warn_store do cog de moderação
from cogs.moderation import warn_store


class Utility(commands.Cog):
    """Comandos de utilidade gerais."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_help_embed(self) -> discord.Embed:
        """Constrói o embed de ajuda."""
        embed = discord.Embed(
            title="📚 Comandos do Nova Era Bot",
            description="Todos os comandos começam com `!`",
            color=config.info
        )
        embed.add_field(
            name="🎯 Gerais",
            value=(
                "`!help` — Mostra esta lista de comandos\n"
                "`!ai [pergunta]` — Conversa com a IA Nova Era\n"
                "`!ai limpar` — Limpa o histórico de conversa do canal\n"
                "`!userinfo [@membro]` — Informações sobre um membro"
            ),
            inline=False
        )
        embed.add_field(
            name="🛡️ Moderação",
            value=(
                "`!ban @membro [dias] [motivo]` — Bane um membro (dias de mensagens: 0-7)\n"
                "`!kick @membro [motivo]` — Expulsa um membro\n"
                "`!timeout @membro [minutos] [motivo]` — Silencia temporariamente\n"
                "`!warn @membro [motivo]` — Adverte um membro\n"
                "`!warns @membro` — Lista as advertências de um membro\n"
                "`!clear [quantidade] [@membro]` — Apaga mensagens do canal"
            ),
            inline=False
        )
        embed.set_footer(text="Mencione um membro entre colchetes quando aplicável.")
        return embed

    @commands.command(name="help", aliases=["helpnova"])
    async def help_command(self, ctx: commands.Context):
        """Mostra a lista de comandos.
        
        Uso: `!help` ou `!helpnova`
        """
        await ctx.send(embed=self.build_help_embed())

    @commands.command(name="userinfo")
    async def userinfo_command(self, ctx: commands.Context, membro: Optional[discord.Member] = None):
        """Mostra informações sobre um membro.
        
        Uso: `!userinfo [@membro]`
        Se nenhum membro for especificado, mostra suas próprias informações.
        """
        alvo = membro or ctx.author
        avisos = warn_store.get(ctx.guild.id, {}).get(alvo.id, [])

        embed = discord.Embed(title=f"👤 {alvo}", color=config.info)
        embed.set_thumbnail(url=alvo.display_avatar.url)
        embed.add_field(name="ID", value=str(alvo.id), inline=True)
        
        if hasattr(alvo, "created_at") and getattr(alvo, "created_at", None):
            embed.add_field(
                name="Conta criada em",
                value=f"<t:{int(alvo.created_at.timestamp())}:D>",
                inline=True
            )

        if isinstance(alvo, discord.Member):
            if alvo.joined_at:
                embed.add_field(
                    name="Entrou no servidor",
                    value=f"<t:{int(alvo.joined_at.timestamp())}:D>",
                    inline=True
                )
            cargo_top = alvo.top_role.name if alvo.top_role.name != "@everyone" else "Nenhum"
            embed.add_field(name="Cargo mais alto", value=cargo_top, inline=True)
            if alvo.nick:
                embed.add_field(name="Apelido", value=alvo.nick, inline=True)

        embed.add_field(
            name="⚠️ Advertências",
            value="Nenhuma" if not avisos else f"{len(avisos)} advertência(s)",
            inline=True
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping_command(self, ctx: commands.Context):
        """Mostra a latência do bot.
        
        Uso: `!ping`
        """
        latency = round(self.bot.latency * 1000)
        embed = embed_info("🏓 Pong!", f"Latência: **{latency}ms**")
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    async def serverinfo_command(self, ctx: commands.Context):
        """Mostra informações sobre o servidor.
        
        Uso: `!serverinfo`
        """
        guild = ctx.guild
        embed = discord.Embed(title=f"🏰 {guild.name}", color=config.info)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="ID do Servidor", value=str(guild.id), inline=True)
        embed.add_field(name="Criado em", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Dono", value=str(guild.owner), inline=True)
        embed.add_field(name="Membros", value=str(guild.member_count), inline=True)
        embed.add_field(name="Canais", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Cargos", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Nível de Verificação", value=str(guild.verification_level), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="botinfo")
    async def botinfo_command(self, ctx: commands.Context):
        """Mostra informações sobre o bot.
        
        Uso: `!botinfo`
        """
        embed = discord.Embed(title="🤖 Nova Era Bot", color=config.info)
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        embed.add_field(name="Nome", value=self.bot.user.name, inline=True)
        embed.add_field(name="ID", value=str(self.bot.user.id), inline=True)
        embed.add_field(name="Criado em", value=f"<t:{int(self.bot.user.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Servidores", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Latência", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Utility(bot))
    log.info("Cog Utility carregado")
