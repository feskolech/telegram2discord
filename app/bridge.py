import asyncio
import logging
from io import BytesIO
from typing import Dict, Optional, Tuple

import discord
from aiogram import Bot, types


class Bridge:
    def __init__(
        self,
        tg_bot: Bot,
        dc_client: discord.Client,
        channel_map: Dict[int, int],
        retry_delays: list[float],
        channel_username_map: Dict[int, str],
        use_embeds: bool,
        embed_color: int,
    ) -> None:
        self.tg_bot = tg_bot
        self.dc_client = dc_client
        self.channel_map = channel_map
        self.retry_delays = retry_delays
        self.channel_username_map = channel_username_map
        self.use_embeds = use_embeds
        self.embed_color = embed_color
        self._discord_channel_cache: Dict[int, discord.abc.Messageable] = {}
        self._media_groups: Dict[Tuple[int, str], dict] = {}
        self.media_group_delay = 1.2
        self.log = logging.getLogger("bridge")

    async def handle_channel_post(self, message: types.Message) -> None:
        if message.chat is None:
            return

        target_channel_id = self.channel_map.get(message.chat.id)
        if target_channel_id is None:
            return

        if message.media_group_id:
            await self._queue_media_group(target_channel_id, message)
            return

        content = message.text or message.caption or ""
        username = self._resolve_channel_username(message)
        formatted_content = self._format_content(content, username)

        if message.photo:
            await self._send_photo_message(target_channel_id, formatted_content, message)
            return

        if formatted_content:
            await self._send_text_message(target_channel_id, formatted_content)

    async def _send_text_message(self, channel_id: int, content: str) -> None:
        channel = await self._get_discord_channel(channel_id)
        if channel is None:
            return
        await self._with_retries(
            f"send text to Discord channel {channel_id}",
            lambda: self._send_text_payload(channel, content),
        )

    async def _send_photo_message(
        self, channel_id: int, content: Optional[str], message: types.Message
    ) -> None:
        channel = await self._get_discord_channel(channel_id)
        if channel is None:
            return

        photo = message.photo[-1]
        photo_bytes = await self._download_photo_bytes(photo)
        if photo_bytes is None:
            return

        await self._send_files(channel_id, channel, [photo_bytes], content)

    async def _get_discord_channel(
        self, channel_id: int
    ) -> Optional[discord.abc.Messageable]:
        if channel_id in self._discord_channel_cache:
            return self._discord_channel_cache[channel_id]

        await self.dc_client.wait_until_ready()

        channel = self.dc_client.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.dc_client.fetch_channel(channel_id)
            except Exception:
                self.log.exception("Failed to fetch Discord channel %s", channel_id)
                return None

        if channel is None:
            self.log.error("Discord channel %s not found", channel_id)
            return None

        self._discord_channel_cache[channel_id] = channel
        return channel

    async def _queue_media_group(self, channel_id: int, message: types.Message) -> None:
        if message.chat is None or not message.media_group_id:
            return
        key = (message.chat.id, message.media_group_id)
        group = self._media_groups.get(key)
        if group is None:
            group = {"messages": [], "task": None, "channel_id": channel_id}
            self._media_groups[key] = group
        group["messages"].append(message)

        existing_task = group.get("task")
        if existing_task:
            existing_task.cancel()

        group["task"] = asyncio.create_task(self._flush_media_group_after_delay(key))

    async def _flush_media_group_after_delay(self, key: Tuple[int, str]) -> None:
        try:
            await asyncio.sleep(self.media_group_delay)
        except asyncio.CancelledError:
            return

        group = self._media_groups.pop(key, None)
        if not group:
            return
        await self._send_media_group(group["channel_id"], group["messages"])

    async def _send_media_group(self, channel_id: int, messages: list[types.Message]) -> None:
        channel = await self._get_discord_channel(channel_id)
        if channel is None:
            return

        ordered = sorted(messages, key=lambda msg: msg.message_id)
        username = self._resolve_channel_username(ordered[0]) if ordered else None
        caption = self._extract_group_caption(ordered)
        formatted_content = self._format_content(caption, username)

        files_bytes: list[bytes] = []
        for message in ordered:
            if not message.photo:
                continue
            photo = message.photo[-1]
            photo_bytes = await self._download_photo_bytes(photo)
            if photo_bytes is None:
                continue
            files_bytes.append(photo_bytes)

        if not files_bytes:
            if formatted_content:
                await self._send_text_message(channel_id, formatted_content)
            return

        await self._send_files(channel_id, channel, files_bytes, formatted_content)

    def _resolve_channel_username(self, message: types.Message) -> Optional[str]:
        if message.chat is None:
            return None
        username = self.channel_username_map.get(message.chat.id)
        if username:
            return username
        return message.chat.username

    def _format_content(self, content: str, username: Optional[str]) -> Optional[str]:
        parts: list[str] = []
        if content and content.strip():
            parts.append(content)

        footer = self._format_footer(username)
        if footer:
            if parts:
                parts.append("")
            parts.append(footer)

        if not parts:
            return None
        return "\n".join(parts)


    def _format_footer(self, username: Optional[str]) -> Optional[str]:
        if not username:
            return None
        normalized = username.strip()
        if normalized.startswith("https://t.me/"):
            normalized = normalized[len("https://t.me/") :]
        if normalized.startswith("t.me/"):
            normalized = normalized[len("t.me/") :]
        if normalized.startswith("@"):
            normalized = normalized[1:]
        if not normalized:
            return None
        return f"[@{normalized} | t.me](https://t.me/{normalized})"

    def _extract_group_caption(self, messages: list[types.Message]) -> str:
        for message in messages:
            content = message.caption or message.text or ""
            if content.strip():
                return content
        return ""

    async def _download_photo_bytes(self, photo: types.PhotoSize) -> Optional[bytes]:
        buffer = await self._with_retries(
            f"download Telegram photo {photo.file_id}",
            lambda: self.tg_bot.download(photo),
        )
        if buffer is None:
            return None
        if isinstance(buffer, (bytes, bytearray)):
            return bytes(buffer)
        if hasattr(buffer, "getvalue"):
            return buffer.getvalue()
        if hasattr(buffer, "read"):
            data = buffer.read()
            return data if isinstance(data, (bytes, bytearray)) else None
        return None

    async def _send_files(
        self,
        channel_id: int,
        channel: discord.abc.Messageable,
        files_bytes: list[bytes],
        content: Optional[str],
    ) -> None:
        async def send_files() -> None:
            files = [
                discord.File(BytesIO(file_bytes), filename=f"photo_{idx + 1}.jpg")
                for idx, file_bytes in enumerate(files_bytes)
            ]
            if self.use_embeds and content:
                embed = discord.Embed(description=content, color=self.embed_color)
                await channel.send(embed=embed, files=files)
                return
            await channel.send(content=content or None, files=files)

        await self._with_retries(
            f"send files to Discord channel {channel_id}",
            send_files,
        )

    async def _send_text_payload(self, channel: discord.abc.Messageable, content: str) -> None:
        if not self.use_embeds:
            await channel.send(content=content)
            return
        embed = discord.Embed(description=content, color=self.embed_color)
        await channel.send(embed=embed)

    async def _with_retries(self, action: str, coro_factory) -> Optional[object]:
        last_exc: Exception | None = None
        attempts = len(self.retry_delays) + 1
        for attempt in range(attempts):
            try:
                return await coro_factory()
            except Exception as exc:
                last_exc = exc
                if attempt >= len(self.retry_delays):
                    break
                delay = self.retry_delays[attempt]
                self.log.warning("%s failed (attempt %s/%s), retrying in %ss", action, attempt + 1, attempts, delay)
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    self.log.exception("Sleep interrupted during retries for %s", action)
                    break

        if last_exc:
            self.log.exception("%s failed after %s attempts", action, attempts)
        return None
