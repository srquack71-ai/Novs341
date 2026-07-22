"""Cog de IA com suporte a g4f e fallback local."""
from __future__ import annotations
import asyncio
import random
import os
from collections import defaultdict
from typing import Optional
import logging

import discord
from discord.ext import commands

from config import config
from utils.embeds import error as embed_error, success as embed_success, info as embed_info

log = logging.getLogger("NovaEra.AI")

# Tentar importar g4f (opcional)
try:
    import g4f
    from g4f.Provider import Yqcloud, OperaAria
    HAS_G4F = True
except ImportError:
    HAS_G4F = False
    log.warning("g4f não instalado — usando apenas IA local")

BASE_SYSTEM = (
    "Você é Nova Era, um bot de Discord prestativo, amigável e útil. "
    "Responda sempre em português brasileiro de forma natural e concisa."
)

# Histórico por canal: channel_id -> list de dicts
conversation_history: dict[int, list[dict]] = defaultdict(list)


async def local_ai_generate(channel_id: int, username: str, user_message: str) -> str:
    """Gerador de IA local com respostas pré-programadas."""
    history = conversation_history[channel_id]

    msg = (user_message or "").strip()
    lower = msg.lower()

    greetings_in = {"olá", "oi", "eai", "ei", "hello", "hey", "opa"}
    if any(tok in lower.split() for tok in greetings_in):
        reply = random.choice([
            f"Olá, {username}! Como posso ajudar você hoje?",
            "Oi! Me conta o que você quer saber",
            "E aí! Em que posso ajudar?"
        ])
    elif "obrigad" in lower or "valeu" in lower:
        reply = random.choice([
            "Por nada!",
            "De nada — se precisar, estou por aqui!",
            "Imagina, fico feliz em ajudar!"
        ])
    elif "ajuda" in lower or "pode me ajudar" in lower:
        reply = "Claro! Diz pra mim o que você precisa que eu tento ajudar."
    elif "como" in lower and ("vai" in lower or "está" in lower):
        reply = random.choice([
            "Estou bem, obrigado por perguntar! Pronto pra ajudar.",
            "Tudo certo por aqui — e você?"
        ])
    elif "por que" in lower or lower.endswith("?") or "?" in msg:
        reply = random.choice([
            "Boa pergunta — não tenho todos os dados aqui, mas posso sugerir uma direção:",
            "Interessante! Pense nisso assim:",
            "Legal essa pergunta. Uma ideia é considerar o seguinte:"
        ])
        if any(k in lower for k in ("erro", "bug", "falha", "exception")):
            reply += " Verifique os logs, tente reproduzir o erro com um caso mínimo e examine o stack trace."
        elif any(k in lower for k in ("config", "token", "apikey", "env", "variável")):
            reply += " Confirme as variáveis de ambiente e privilégios; muitas falhas vêm daí."
        else:
            reply += " Se quiser, me dá mais contexto e eu tento ajudar melhor."
    else:
        short_echo = (msg if len(msg) <= 120 else msg[:117] + "...")
        reply = random.choice([
            f"Entendi: {short_echo}. Pode explicar mais um pouco?",
            f"Você disse: {short_echo}. Uma sugestão seria decompor o problema em partes menores.",
            f"Interessante. Sobre {short_echo}, você já tentou procurar por exemplos ou testar com casos menores?"
        ])

    history.append({"username": username, "content": user_message, "role": "user"})
    history.append({"username": "Nova Era", "content": reply, "role": "bot"})
    if len(history) > config.max_ai_history:
        del history[:len(history) - config.max_ai_history]

    return reply


async def _call_g4f_in_thread(messages, provider):
    """Chama g4f em thread separada."""
    def sync_call():
        return g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=messages,
            provider=provider
        )
    return await asyncio.to_thread(sync_call)


async def ask_ai(channel_id: int, username: str, user_message: str) -> str:
    """Pergunta à IA (g4f com fallback local)."""
    if not HAS_G4F or config.force_local_ai:
        return await local_ai_generate(channel_id, username, user_message)

    history = conversation_history[channel_id]

    messages = [{"role": "system", "content": BASE_SYSTEM}]
    for h in history:
        if h.get("role") == "user":
            messages.append({"role": "user", "content": f"{h['username']}: {h['content']}"})
        else:
            messages.append({"role": "assistant", "content": h.get("content", "")})
    messages.append({"role": "user", "content": f"{username}: {user_message}"})

    last_error = None
    for provider in (Yqcloud, OperaAria):
        try:
            reply = await asyncio.wait_for(
                _call_g4f_in_thread(messages, provider),
                timeout=config.g4f_timeout
            )
            reply = (reply or "").strip()
            if not reply:
                raise Exception("Resposta vazia do provedor")

            history.append({"username": username, "content": user_message, "role": "user"})
            history.append({"username": "Nova Era", "content": reply, "role": "bot"})
            if len(history) > config.max_ai_history:
                del history[:len(history) - config.max_ai_history]

            return reply
        except asyncio.TimeoutError:
            last_error = Exception(f"Timeout de {config.g4f_timeout}s ao chamar {provider.__name__}")
            log.warning(f"{provider.__name__} timeout.")
        except Exception as e:
            last_error = e
            log.warning(f"{provider.__name__} falhou: {e}")
        await asyncio.sleep(1)

    log.info("Todos provedores g4f falharam — usando IA local como fallback.")
    try:
        return await local_ai_generate(channel_id, username, user_message)
    except Exception as e:
        log.error(f"IA local também falhou: {e}")
        raise last_error or e or Exception("IA indisponível")


def clear_history(channel_id: int):
    """Limpa o histórico de conversa de um canal."""
    conversation_history[channel_id].clear()


class AI(commands.Cog):
    """Comandos de IA e conversa."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ai", aliases=["ask"])
    async def ai_command(self, ctx: commands.Context, *, args: str = ""):
        """Conversa com a IA Nova Era.
        
        Uso:
        - `!ai [pergunta]` — Faz uma pergunta
        - `!ai limpar` — Limpa o histórico do canal
        """
        if args.strip().lower() == "limpar":
            clear_history(ctx.channel.id)
            await ctx.send(embed=embed_success("Histórico limpo", "O histórico de conversa deste canal foi limpo."))
            return

        if not args.strip():
            await ctx.send(
                embed=embed_info(
                    "Como usar",
                    "Use `!ai [sua pergunta]` para conversar.\n"
                    "Use `!ai limpar` para limpar o histórico."
                )
            )
            return

        async with ctx.typing():
            try:
                resposta = await ask_ai(ctx.channel.id, ctx.author.name, args)
                if len(resposta) <= 1900:
                    embed = discord.Embed(color=config.info)
                    embed.set_author(name=f"{ctx.author.display_name} perguntou:")
                    embed.description = f"> {args}\n\n{resposta}"
                    embed.set_footer(text="Nova Era IA")
                    await ctx.send(embed=embed)
                else:
                    chunks = [resposta[i:i+1900] for i in range(0, len(resposta), 1900)]
                    await ctx.send(f"{ctx.author.display_name} perguntou: {args}\n\n{chunks[0]}")
                    for chunk in chunks[1:]:
                        await ctx.send(chunk)
            except Exception as e:
                log.error(f"comando !ai falhou: {e}")
                await ctx.send(embed=embed_error("Erro", "A IA está indisponível no momento. Tente novamente."))

    @ai_command.error
    async def ai_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handler de erros para o comando !ai."""
        await ctx.send(embed=embed_error("Erro", f"Erro ao processar comando: {error}"))


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(AI(bot))
    log.info("Cog AI carregado")
