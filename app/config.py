import os
from dataclasses import dataclass
from typing import Dict, List


def _get_env(name: str, *, required: bool = False, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_int_list(value: str | None) -> List[int]:
    if not value:
        return []
    items: List[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        items.append(int(part))
    return items


def _parse_float_list(value: str | None) -> List[float]:
    if not value:
        return []
    items: List[float] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        items.append(float(part))
    return items


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_color(value: str | None, default: int) -> int:
    if not value:
        return default
    raw = value.strip().lower()
    if raw.startswith("#"):
        raw = raw[1:]
    if raw.startswith("0x"):
        return int(raw, 16)
    try:
        return int(raw, 16) if all(ch in "0123456789abcdef" for ch in raw) else int(raw)
    except ValueError:
        return default


def _parse_channel_map() -> Dict[int, int]:
    raw = os.getenv("CHANNEL_MAP")
    if raw:
        mapping: Dict[int, int] = {}
        for pair in raw.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                raise RuntimeError(
                    "CHANNEL_MAP must be in format tg_id:discord_id,tg_id2:discord_id2"
                )
            tg_id, dc_id = pair.split(":", 1)
            mapping[int(tg_id.strip())] = int(dc_id.strip())
        if not mapping:
            raise RuntimeError("CHANNEL_MAP is set but empty")
        return mapping

    tg_id = _get_env("TELEGRAM_SOURCE_CHANNEL_ID", required=True)
    dc_id = _get_env("DISCORD_TARGET_CHANNEL_ID", required=True)
    return {int(tg_id): int(dc_id)}


def _parse_username_map() -> Dict[int, str]:
    raw = os.getenv("CHANNEL_USERNAME_MAP")
    if raw:
        mapping: Dict[int, str] = {}
        for pair in raw.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                raise RuntimeError(
                    "CHANNEL_USERNAME_MAP must be in format tg_id:username,tg_id2:username2"
                )
            tg_id, username = pair.split(":", 1)
            mapping[int(tg_id.strip())] = username.strip()
        if not mapping:
            raise RuntimeError("CHANNEL_USERNAME_MAP is set but empty")
        return mapping

    username = os.getenv("TELEGRAM_SOURCE_CHANNEL_USERNAME")
    if username:
        tg_id = _get_env("TELEGRAM_SOURCE_CHANNEL_ID", required=True)
        return {int(tg_id): username.strip()}

    return {}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    discord_bot_token: str
    channel_map: Dict[int, int]
    channel_username_map: Dict[int, str]
    allowed_admin_ids: List[int]
    log_level: str
    retry_delays: List[float]
    use_embeds: bool
    embed_color: int


def load_settings() -> Settings:
    telegram_bot_token = _get_env("TELEGRAM_BOT_TOKEN", required=True)
    discord_bot_token = _get_env("DISCORD_BOT_TOKEN", required=True)
    channel_map = _parse_channel_map()
    channel_username_map = _parse_username_map()
    allowed_admin_ids = _parse_int_list(os.getenv("ALLOWED_ADMIN_IDS", ""))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    retry_delays = _parse_float_list(os.getenv("RETRY_DELAYS", ""))
    if not retry_delays:
        retry_delays = [2, 4, 8, 16, 32]
    use_embeds = _parse_bool(os.getenv("USE_EMBEDS"), default=False)
    embed_color = _parse_color(os.getenv("EMBED_COLOR"), default=0x5865F2)
    return Settings(
        telegram_bot_token=telegram_bot_token,
        discord_bot_token=discord_bot_token,
        channel_map=channel_map,
        channel_username_map=channel_username_map,
        allowed_admin_ids=allowed_admin_ids,
        log_level=log_level,
        retry_delays=retry_delays,
        use_embeds=use_embeds,
        embed_color=embed_color,
    )
