#!/usr/bin/env python3
# Dependências: discord.py, g4f
# Instale: pip install discord.py g4f

import os
import random
import asyncio
from datetime import timedelta, datetime
from collections import defaultdict
from typing import Optional

import discord
import g4f
from g4f.Provider import Yqcloud, OperaAria
from discord.ext import commands

# ─── Config ───────────────────────────────────────────────────────────────────

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── Help embed ───────────────────────────────────────────────────────────────

def build_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Comandos do Nova Era Bot",
        description="Todos os comandos começam com `!`",
        color=0x5865F2
    )
    embed.add_field(
        name="Gerais",
        value=(
            "`!helpNova` — Mostra esta lista de comandos\n"
            "`!ai [pergunta]` — Conversa com a IA Nova Era\n"
            "`!ai limpar` — Limpa o histórico de conversa do canal\n"
            "`!userinfo [@membro]` — Informações sobre um membro"
        ),
        inline=False
    )
    embed.add_field(
        name="Moderação",
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

# ─── IA (g4f + fallback local) ────────────────────────────────────────────────

BASE_SYSTEM = (
    "Você é Nova Era, um bot de Discord prestativo, amigável e útil. "
    "Responda sempre em português brasileiro de forma natural e concisa."
)

MAX_HISTORY = 8
G4F_TIMEOUT = 25  # segundos por provedor

# Histórico por canal: channel_id -> list de dicts
conversation_history: dict[int, list[dict]] = defaultdict(list)


async def local_ai_generate(channel_id: int, username: str, user_message: str) -> str:
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
    if len(history) > MAX_HISTORY:
        del history[:len(history) - MAX_HISTORY]

    return reply


async def _call_g4f_in_thread(messages, provider):
    def sync_call():
        return g4f.ChatCompletion.create(model=g4f.models.default, messages=messages, provider=provider)
    return await asyncio.to_thread(sync_call)


async def ask_ai(channel_id: int, username: str, user_message: str) -> str:
    if os.environ.get("FORCE_LOCAL", "") == "1":
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
            reply = await asyncio.wait_for(_call_g4f_in_thread(messages, provider), timeout=G4F_TIMEOUT)
            reply = (reply or "").strip()
            if not reply:
                raise Exception("Resposta vazia do provedor")

            history.append({"username": username, "content": user_message, "role": "user"})
            history.append({"username": "Nova Era", "content": reply, "role": "bot"})
            if len(history) > MAX_HISTORY:
                del history[:len(history) - MAX_HISTORY]

            return reply
        except asyncio.TimeoutError:
            last_error = Exception(f"Timeout de {G4F_TIMEOUT}s ao chamar {provider.__name__}")
            print(f"[AVISO] {provider.__name__} timeout.")
        except Exception as e:
            last_error = e
            print(f"[AVISO] {provider.__name__} falhou: {e}")
        await asyncio.sleep(1)

    print("[INFO] Todos provedores g4f falharam — usando IA local como fallback.")
    try:
        return await local_ai_generate(channel_id, username, user_message)
    except Exception as e:
        print(f"[ERRO] IA local também falhou: {e}")
        raise last_error or e or Exception("IA indisponível")


def clear_history(channel_id: int):
    conversation_history[channel_id].clear()


# ─── Eventos ──────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"Nova Era online como {bot.user} ({bot.user.id})")


# Apenas processa comandos com prefixo "!"
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)


# ─── Boas-vindas ao entrar no servidor ───────────────────────────────────────

@bot.event
async def on_member_join(member: discord.Member):
    welcome_text = (
        "Bem-vindo à Nova Era.\n\n"
        "Sua jornada começa agora. Participe das nossas noites de jogos, interaja com a comunidade e faça novas amizades.\n\n"
        "Antes de seguir, confira os canais #seja-booster e #leveis・levels para conhecer todas as vantagens e recompensas disponíveis.\n\n"
        "O futuro começa aqui."
    )

    text_to_send = welcome_text  # sem menção, conforme pedido
    guild = member.guild

    # 1) Procura canal "geral"
    candidates = ["chat geral", "chat-geral", "geral", "general"]
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
            await target_channel.send(text_to_send)
            sent = True
        except Exception as e:
            print(f"[AVISO] Falha ao enviar boas-vindas em canal {target_channel}: {e}")

    # 4) DM como último recurso
    if not sent:
        try:
            await member.send(welcome_text)
        except Exception as e:
            print(f"[AVISO] Não foi possível enviar DM ao membro {member}: {e}")


# ─── Comando !helpNova ────────────────────────────────────────────────────────

@bot.command(name="helpNova", aliases=["help"])
async def help_nova(ctx: commands.Context):
    await ctx.send(embed=build_help_embed())


# ─── Comando !ai ──────────────────────────────────────────────────────────────

@bot.command(name="ai")
async def ai_command(ctx: commands.Context, *, args: str = ""):
    if args.strip().lower() == "limpar":
        clear_history(ctx.channel.id)
        await ctx.send("Histórico de conversa deste canal foi limpo.")
        return

    if not args.strip():
        await ctx.send(
            "Use `!ai [sua pergunta]` para conversar.\n"
            "Use `!ai limpar` para limpar o histórico."
        )
        return

    async with ctx.typing():
        try:
            resposta = await ask_ai(ctx.channel.id, ctx.author.name, args)
            if len(resposta) <= 1900:
                embed = discord.Embed(color=0x5865F2)
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
            print(f"[ERRO] comando !ai falhou: {e}")
            await ctx.send("A IA está indisponível no momento. Tente novamente.")


# ─── Comando !ban ─────────────────────────────────────────────────────────────

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_command(ctx: commands.Context, membro: discord.Member, dias: int = 0, *, motivo: str = "Sem motivo informado"):
    if not membro.is_bannable():
        await ctx.send("Não consigo banir esse membro (cargo superior ou igual ao meu).")
        return

    dias = max(0, min(dias, 7))
    try:
        await membro.ban(delete_message_days=dias, reason=motivo)
        embed = discord.Embed(title="Membro Banido", color=0xFF0000)
        embed.add_field(name="Membro", value=str(membro), inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=True)
        embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
        await ctx.send(embed=embed)
        try:
            await membro.send(f"Você foi banido do servidor {ctx.guild.name}.\nMotivo: {motivo}")
        except Exception:
            pass
    except Exception as e:
        print(f"[ERRO] ao banir: {e}")
        await ctx.send("Erro ao banir o membro.")

@ban_command.error
async def ban_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para banir membros.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Uso correto: `!ban @membro [dias] [motivo]`")
    else:
        await ctx.send("Erro ao processar o comando ban.")


# ─── Comando !kick ────────────────────────────────────────────────────────────

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_command(ctx: commands.Context, membro: discord.Member, *, motivo: str = "Sem motivo informado"):
    if not membro.is_kickable():
        await ctx.send("Não consigo expulsar esse membro (cargo superior ou igual ao meu).")
        return

    try:
        await membro.kick(reason=motivo)
        embed = discord.Embed(title="Membro Expulso", color=0xFF8800)
        embed.add_field(name="Membro", value=str(membro), inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=True)
        embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
        await ctx.send(embed=embed)
        try:
            await membro.send(f"Você foi expulso do servidor {ctx.guild.name}.\nMotivo: {motivo}")
        except Exception:
            pass
    except Exception as e:
        print(f"[ERRO] ao expulsar: {e}")
        await ctx.send("Erro ao expulsar o membro.")

@kick_command.error
async def kick_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para expulsar membros.")
    else:
        await ctx.send("Erro ao processar o comando kick.")


# ─── Comando !timeout ─────────────────────────────────────────────────────────

@bot.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout_command(ctx: commands.Context, membro: discord.Member, minutos: int = 10, *, motivo: str = "Sem motivo informado"):
    minutos = max(1, min(minutos, 40320))
    try:
        await membro.timeout(timedelta(minutes=minutos), reason=motivo)
        duracao = f"{minutos // 60}h {minutos % 60}min" if minutos >= 60 else f"{minutos} minutos"
        embed = discord.Embed(title="Membro Silenciado", color=0xFFCC00)
        embed.add_field(name="Membro", value=str(membro), inline=True)
        embed.add_field(name="Duração", value=duracao, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.add_field(name="Moderador", value=str(ctx.author), inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"[ERRO] ao aplicar timeout: {e}")
        await ctx.send("Erro ao silenciar o membro.")

@timeout_command.error
async def timeout_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para silenciar membros.")
    else:
        await ctx.send("Erro ao processar o comando timeout.")


# ─── Advertências ─────────────────────────────────────────────────────────────

warn_store: dict[int, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))

@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_command(ctx: commands.Context, membro: discord.Member, *, motivo: str):
    warn_store[ctx.guild.id][membro.id].append({
        "motivo": motivo,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "moderador": str(ctx.author)
    })
    total = len(warn_store[ctx.guild.id][membro.id])

    embed = discord.Embed(title="Advertência Aplicada", color=0xFFA500)
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
async def warn_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para advertir membros.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Uso correto: `!warn @membro [motivo]`")
    else:
        await ctx.send("Erro ao processar o comando warn.")


@bot.command(name="warns")
@commands.has_permissions(moderate_members=True)
async def warns_command(ctx: commands.Context, membro: discord.Member):
    avisos = warn_store.get(ctx.guild.id, {}).get(membro.id, [])
    if not avisos:
        await ctx.send(f"{membro} não possui advertências.")
        return

    desc = "\n\n".join(
        f"**{i+1}.** {w['motivo']}\n> Por {w['moderador']} em {w['data']}"
        for i, w in enumerate(avisos)
    )
    embed = discord.Embed(title=f"Advertências de {membro}", description=desc, color=0xFFA500)
    embed.set_footer(text=f"Total: {len(avisos)} advertência(s)")
    await ctx.send(embed=embed)

@warns_command.error
async def warns_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para ver advertências.")
    else:
        await ctx.send("Erro ao processar o comando warns.")


# ─── Comando !clear ───────────────────────────────────────────────────────────

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_command(ctx: commands.Context, quantidade: int = 10, membro: Optional[discord.Member] = None):
    quantidade = max(1, min(quantidade, 100))

    # tenta deletar a mensagem de invocação (silenciosa se não for possível)
    try:
        await ctx.message.delete()
    except Exception:
        pass

    def check(msg):
        return membro is None or msg.author == membro

    try:
        deleted = await ctx.channel.purge(limit=quantidade if membro is None else 200, check=check)
        deleted = deleted[:quantidade]
        msg = await ctx.send(
            f"{len(deleted)} mensagem(s) apagada(s)" + (f" de {membro}" if membro else "") + "."
        )
        await asyncio.sleep(4)
        try:
            await msg.delete()
        except Exception:
            pass
    except Exception as e:
        print(f"[ERRO] ao apagar mensagens: {e}")
        await ctx.send("Erro ao apagar mensagens.")

@clear_command.error
async def clear_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para apagar mensagens.")
    else:
        await ctx.send("Erro ao processar o comando clear.")


# ─── Comando !userinfo ────────────────────────────────────────────────────────

@bot.command(name="userinfo")
async def userinfo_command(ctx: commands.Context, membro: Optional[discord.Member] = None):
    alvo = membro or ctx.author
    avisos = warn_store.get(ctx.guild.id, {}).get(alvo.id, [])

    embed = discord.Embed(title=f"{alvo}", color=0x5865F2)
    embed.set_thumbnail(url=alvo.display_avatar.url)
    embed.add_field(name="ID", value=str(alvo.id), inline=True)
    if hasattr(alvo, "created_at") and getattr(alvo, "created_at", None):
        embed.add_field(name="Conta criada em", value=f"<t:{int(alvo.created_at.timestamp())}:D>", inline=True)

    if isinstance(alvo, discord.Member):
        if alvo.joined_at:
            embed.add_field(name="Entrou no servidor", value=f"<t:{int(alvo.joined_at.timestamp())}:D>", inline=True)
        cargo_top = alvo.top_role.name if alvo.top_role.name != "@everyone" else "Nenhum"
        embed.add_field(name="Cargo mais alto", value=cargo_top, inline=True)
        if alvo.nick:
            embed.add_field(name="Apelido", value=alvo.nick, inline=True)

    embed.add_field(
        name="Advertências",
        value="Nenhuma" if not avisos else f"{len(avisos)} advertência(s)",
        inline=True
    )
    embed.timestamp = discord.utils.utcnow()
    await ctx.send(embed=embed)


# ─── Iniciar ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("[ERRO] DISCORD_BOT_TOKEN não definido!")
        exit(1)
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar o bot: {e}")
