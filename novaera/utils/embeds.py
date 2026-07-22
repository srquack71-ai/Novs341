"""Helpers de embed reutilizáveis por todos os cogs."""
from __future__ import annotations
import discord
from config import config


def base_embed(title: str = "", description: str = "", color: int | None = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=color if color is not None else config.color,
    )


def success(title: str = "Sucesso", description: str = "") -> discord.Embed:
    return base_embed(f"✅ {title}", description, config.success)


def error(title: str = "Erro", description: str = "") -> discord.Embed:
    return base_embed(f"❌ {title}", description, config.error)


def warn(title: str = "Atenção", description: str = "") -> discord.Embed:
    return base_embed(f"⚠️ {title}", description, config.warn)


def info(title: str = "Informação", description: str = "") -> discord.Embed:
    return base_embed(f"ℹ️ {title}", description, config.info)


def paginated(embeds: list[discord.Embed]) -> list[discord.Embed]:
    total = len(embeds)
    for i, e in enumerate(embeds, 1):
        e.set_footer(text=f"Página {i}/{total} • NovaEra")
    return embeds
