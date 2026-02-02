import asyncio
import logging

import discord
from aiogram import Bot, Dispatcher, Router, types

from app.bridge import Bridge
from app.config import load_settings
from app.logging_setup import setup_logging


async def _run() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    log = logging.getLogger("main")

    tg_bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    router = Router()
    dp.include_router(router)

    intents = discord.Intents.none()
    intents.guilds = True
    dc_client = discord.Client(intents=intents)

    bridge = Bridge(
        tg_bot,
        dc_client,
        settings.channel_map,
        settings.retry_delays,
        settings.channel_username_map,
        settings.use_embeds,
        settings.embed_color,
    )

    @router.channel_post()
    async def on_channel_post(message: types.Message) -> None:
        await bridge.handle_channel_post(message)

    @dc_client.event
    async def on_ready() -> None:
        log.info("Discord bot connected as %s", dc_client.user)

    async def start_discord() -> None:
        await dc_client.start(settings.discord_bot_token)

    async def start_telegram() -> None:
        await dp.start_polling(tg_bot)

    discord_task = asyncio.create_task(start_discord())
    telegram_task = asyncio.create_task(start_telegram())

    done, pending = await asyncio.wait(
        [discord_task, telegram_task], return_when=asyncio.FIRST_EXCEPTION
    )

    for task in done:
        if task.exception():
            log.error("Task failed: %s", task.exception())

    for task in pending:
        task.cancel()

    await tg_bot.session.close()
    await dc_client.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
