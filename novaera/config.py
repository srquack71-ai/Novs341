"""Configuração central do NovaEraBot."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _get_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("1", "true", "yes", "on", "y")

@dataclass
class Config:
    # Token e Prefixo
    token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    prefix: str = field(default_factory=lambda: os.getenv("PREFIX", "!"))
    
    # IA (OpenAI ou g4f)
    ai_provider: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai"))
    ai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    ai_model: str = field(default_factory=lambda: os.getenv("AI_MODEL", "gpt-4o-mini"))
    ai_fallback_model: str = field(default_factory=lambda: os.getenv("AI_FALLBACK_MODEL", "gpt-3.5-turbo"))
    force_local_ai: bool = field(default_factory=lambda: _get_bool("FORCE_LOCAL_AI", False))
    
    # Dono
    owner_id: int = field(default_factory=lambda: int(os.getenv("OWNER_ID", "0")))
    
    # Presença
    status: str = field(default_factory=lambda: os.getenv("BOT_STATUS", "online"))
    activity_type: str = field(default_factory=lambda: os.getenv("BOT_ACTIVITY_TYPE", "playing").lower())
    activity: str = field(default_factory=lambda: os.getenv("BOT_ACTIVITY", "NovaEra | !help"))
    
    # Banco de dados
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "database/database.db"))
    
    # Cores padrão (hex -> int)
    color: int = 0x2B2D31
    success: int = 0x57F287
    error: int = 0xED4245
    warn: int = 0xFEE75C
    info: int = 0x5865F2
    
    # Economia
    daily_amount: int = 500
    work_min: int = 100
    work_max: int = 400
    work_cooldown: int = 3600
    daily_cooldown: int = 86400
    rob_cooldown: int = 7200
    rob_success_chance: float = 0.45
    
    # XP / Níveis
    xp_per_message: int = field(default_factory=lambda: int(os.getenv("XP_PER_MESSAGE", "15")))
    xp_cooldown: int = 60
    level_up_base: int = 100
    level_up_mult: float = 1.5
    
    # Auto-mod defaults
    automod_antispam: bool = True
    automod_antiflood: bool = True
    automod_antilinks: bool = False
    automod_antiinvite: bool = True
    
    # IA - Histórico
    max_ai_history: int = 8
    g4f_timeout: int = 25

    @property
    def activity_enum(self):
        import discord
        mapping = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing,
            "streaming": discord.ActivityType.streaming,
        }
        return mapping.get(self.activity_type, discord.ActivityType.playing)

    @property
    def status_enum(self):
        import discord
        mapping = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }
        return mapping.get(self.status, discord.Status.online)

config = Config()
