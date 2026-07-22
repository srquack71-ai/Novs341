"""Cog de moderação com comandos de ban, kick, timeout e warn."""
from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands

from config import config
from utils.embeds import error as embed_error, success as embed_success, warn as embed_warn
from utils.checks import is_mod

log = logging.getLogger("NovaEra.Moderation")

# Armazena advertências em memória: {guild_id: {user_id: [{"motivo": "", "data": "", "moderador": ""}]}}
warn_store: dict[int, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))


class Moderation(commands.Cog):
    """Comandos de moderação."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_command(self, ctx: commands.Context, membro: discord.Member, dias: int = 0, *, motivo: str = "Sem motivo informado"):
        """Bane um membro do servidor.
        
        Uso: `!ban @membro [dias] [motivo]`
        - dias: 0-7 (quantos dias de mensagens deletar)
        """
        if not membro.is_bannable():
            await ctx.send(embed=embed_error("Erro", "Não consigo banir esse membro (cargo superior ou igual ao meu)."))
            return

        dias = max(0, min(dias, 7))
        try:
            await membro.ban(delete_message_days=dias, reason=motivo)
            embed = discord.Embed(title="🔨 Membro Banido", color=config.error)
            embed.add_field(name="Membro", value=str(membro), inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=True)
            embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
            embed.add_field(name="Dias de mensagens deletadas", value=str(dias), inline=True)
            await ctx.send(embed=embed)
            try:
                await membro.send(f"Você foi banido do servidor {ctx.guild.name}.\nMotivo: {motivo}")
            except Exception:
                pass
        except Exception as e:
            log.error(f"Erro ao banir: {e}")
            await ctx.send(embed=embed_error("Erro", "Erro ao banir o membro."))

    @ban_command.error
    async def ban_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Sem permissão", "Você não tem permissão para banir membros."))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=embed_error("Argumento faltando", "Uso correto: `!ban @membro [dias] [motivo]`"))
        else:
            await ctx.send(embed=embed_error("Erro", f"Erro ao processar o comando ban: {error}"))

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_command(self, ctx: commands.Context, membro: discord.Member, *, motivo: str = "Sem motivo informado"):
        """Expulsa um membro do servidor.
        
        Uso: `!kick @membro [motivo]`
        """
        if not membro.is_kickable():
            await ctx.send(embed=embed_error("Erro", "Não consigo expulsar esse membro (cargo superior ou igual ao meu)."))
            return

        try:
            await membro.kick(reason=motivo)
            embed = discord.Embed(title="👢 Membro Expulso", color=0xFF8800)
            embed.add_field(name="Membro", value=str(membro), inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=True)
            embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
            await ctx.send(embed=embed)
            try:
                await membro.send(f"Você foi expulso do servidor {ctx.guild.name}.\nMotivo: {motivo}")
            except Exception:
                pass
        except Exception as e:
            log.error(f"Erro ao expulsar: {e}")
            await ctx.send(embed=embed_error("Erro", "Erro ao expulsar o membro."))

    @kick_command.error
    async def kick_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Sem permissão", "Você não tem permissão para expulsar membros."))
        else:
            await ctx.send(embed=embed_error("Erro", f"Erro ao processar o comando kick: {error}"))

    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout_command(self, ctx: commands.Context, membro: discord.Member, minutos: int = 10, *, motivo: str = "Sem motivo informado"):
        """Silencia temporariamente um membro.
        
        Uso: `!timeout @membro [minutos] [motivo]`
        - minutos: 1-40320 (até 28 dias)
        """
        minutos = max(1, min(minutos, 40320))
        try:
            await membro.timeout(timedelta(minutes=minutos), reason=motivo)
            duracao = f"{minutos // 60}h {minutos % 60}min" if minutos >= 60 else f"{minutos} minutos"
            embed = discord.Embed(title="🔇 Membro Silenciado", color=config.warn)
            embed.add_field(name="Membro", value=str(membro), inline=True)
            embed.add_field(name="Duração", value=duracao, inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=False)
            embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            log.error(f"Erro ao aplicar timeout: {e}")
            await ctx.send(embed=embed_error("Erro", "Erro ao silenciar o membro."))

    @timeout_command.error
    async def timeout_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Sem permissão", "Você não tem permissão para silenciar membros."))
        else:
            await ctx.send(embed=embed_error("Erro", f"Erro ao processar o comando timeout: {error}"))

    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn_command(self, ctx: commands.Context, membro: discord.Member, *, motivo: str = "Sem motivo informado"):
        """Adverte um membro.
        
        Uso: `!warn @membro [motivo]`
        """
        warn_store[ctx.guild.id][membro.id].append({
            "motivo": motivo,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "moderador": str(ctx.author)
        })
        total = len(warn_store[ctx.guild.id][membro.id])

        embed = discord.Embed(title="⚠️ Advertência Aplicada", color=config.warn)
        embed.add_field(name="Membro", value=str(membro), inline=True)
        embed.add_field(name="Total de Avisos", value=str(total), inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
        await ctx.send(embed=embed)

        try:
            await membro.send(
                f"Você recebeu uma advertência no servidor {ctx.guild.name}.\n"
                f"Motivo: {motivo}\nTotal de advertências: {total}"
            )
        except Exception:
            pass

    @warn_command.error
    async def warn_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Sem permissão", "Você não tem permissão para advertir membros."))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=embed_error("Argumento faltando", "Uso correto: `!warn @membro [motivo]`"))
        else:
            await ctx.send(embed=embed_error("Erro", f"Erro ao processar o comando warn: {error}"))

    @commands.command(name="warns")
    @commands.has_permissions(moderate_members=True)
    async def warns_command(self, ctx: commands.Context, membro: discord.Member):
        """Lista as advertências de um membro.
        
        Uso: `!warns @membro`
        """
        avisos = warn_store.get(ctx.guild.id, {}).get(membro.id, [])
        if not avisos:
            await ctx.send(embed=embed_success("Sem avisos", f"{membro} não possui advertências."))
            return

        desc = "\n\n".join(
            f"**{i+1}.** {w['motivo']}\n> Por {w['moderador']} em {w['data']}"
            for i, w in enumerate(avisos)
        )
        embed = discord.Embed(title=f"⚠️ Advertências de {membro}", description=desc, color=config.warn)
        embed.set_footer(text=f"Total: {len(avisos)} advertência(s)")
        await ctx.send(embed=embed)

    @warns_command.error
    async def warns_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Sem permissão", "Você não tem permissão para ver advertências."))
        else:
            await ctx.send(embed=embed_error("Erro", f"Erro ao processar o comando warns: {error}"))

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_command(self, ctx: commands.Context, quantidade: int = 10, membro: Optional[discord.Member] = None):
        """Apaga mensagens do canal.
        
        Uso: `!clear [quantidade] [@membro]`
        - quantidade: 1-100 mensagens
        """
        quantidade = max(1, min(quantidade, 100))

        # Tenta deletar a mensagem de invocação
        try:
            await ctx.message.delete()
        except Exception:
            pass

        def check(msg):
            return membro is None or msg.author == membro

        try:
            deleted = await ctx.channel.purge(
                limit=quantidade if membro is None else 200,
                check=check
            )
            deleted = deleted[:quantidade]
            info_text = f"{len(deleted)} mensagem(s) apagada(s)"
            if membro:
                info_text += f" de {membro}"
            info_text += "."
            
            msg = await ctx.send(embed=embed_success("Mensagens apagadas", info_text, delete_after=4))
            await msg.delete()
        except Exception as e:
            log.error(f"Erro ao apagar mensagens: {e}")
            await ctx.send(embed=embed_error("Erro", "Erro ao apagar mensagens."))

    @clear_command.error
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Sem permissão", "Você não tem permissão para apagar mensagens."))
        else:
            await ctx.send(embed=embed_error("Erro", f"Erro ao processar o comando clear: {error}"))


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Moderation(bot))
    log.info("Cog Moderation carregado")
