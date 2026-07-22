"""Cog de boas-vindas."""
from __future__ import annotations
import logging
from typing import Optional

import discord
from discord.ext import commands

from config import config
from utils.embeds import info as embed_info

log = logging.getLogger("NovaEra.Welcome")


class Welcome(commands.Cog):
    """Gerencia mensagens de boas-vindas."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Envia mensagem de boas-vindas quando um membro entra."""
        welcome_text = (
            f"Bem-vindo à **{member.guild.name}**!\n\n"
            f"Olá {member.mention}, sua jornada começa agora. "
            "Participe das nossas atividades, interaja com a comunidade e faça novas amizades.\n\n"
            "Confira os canais de informações para conhecer todas as vantagens e recompensas disponíveis.\n\n"
            "O futuro começa aqui. 🚀"
        )

        guild = member.guild

        # 1) Procura canal "geral"
        candidates = ["chat geral", "chat-geral", "geral", "general", "bem-vindo"]
        target_channel: Optional[discord.TextChannel] = None
        for name in candidates:
            for ch in guild.text_channels:
                if ch.name.lower() == name and ch.permissions_for(guild.me).send_messages:
                    target_channel = ch
                    break
            if target_channel:
                break

        # 2) System channel
        if not target_channel and guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            target_channel = guild.system_channel

        # 3) Primeiro canal com permissão
        if not target_channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    target_channel = ch
                    break

        sent = False
        if target_channel:
            try:
                embed = embed_info(f"Bem-vindo(a), {member.name}!", welcome_text)
                embed.set_thumbnail(url=member.display_avatar.url)
                await target_channel.send(embed=embed)
                sent = True
            except Exception as e:
                log.warning(f"Falha ao enviar boas-vindas em canal {target_channel}: {e}")

        # 4) DM como último recurso
        if not sent:
            try:
                embed = embed_info("Bem-vindo(a)!", welcome_text)
                embed.set_thumbnail(url=member.display_avatar.url)
                await member.send(embed=embed)
            except Exception as e:
                log.warning(f"Não foi possível enviar DM ao membro {member}: {e}")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(Welcome(bot))
    log.info("Cog Welcome carregado")
