# tg2ds

Telegram → Discord bridge bot (aiogram + discord.py). It forwards **new** posts from a Telegram channel to a Discord channel.

## Features
- Text + photos (highest resolution photo is used).
- Albums (media groups) are sent as **one** Discord message with multiple attachments.
- Text is sent as an embed (colored sidebar) when `USE_EMBEDS=1`.
- A clickable footer `@channel | t.me` is appended when the channel username is known.

## Requirements
- Docker and docker‑compose on your server/VPS.
- Telegram bot is **admin** in the source channel.
- Discord bot is added to the server and has `View Channel`, `Send Messages`, `Attach Files` permissions.

## How to get tokens and IDs
### Telegram Bot Token
1) In Telegram open @BotFather → `/newbot`.
2) Create a bot and copy the token.
3) Add the bot to the channel and make it **admin**.

### Telegram Channel ID
Option 1 (simple):
1) Forward any message from the channel to @userinfobot.
2) It will return the channel `ID` (usually starts with `-100`).

Option 2:
1) Forward a message from the channel to @getmyid_bot.
2) It will show the `chat_id`.

### Discord Bot Token
1) Open Discord Developer Portal → your application.
2) **Bot** section → `Reset Token` → copy the token.

### Invite Discord bot to server
1) Developer Portal → **OAuth2 → URL Generator**.
2) Scopes: **bot**.
3) Bot Permissions: `View Channels`, `Send Messages`, `Attach Files`.
4) Open the generated URL and add the bot to your server.

### Discord Channel ID
1) Enable **Developer Mode** in Discord (User Settings → Advanced).
2) Right‑click the channel → **Copy ID**.

## Quick start
1) Copy `.env.example` to `.env` and fill it in.
2) Run:
```bash
docker-compose up -d
```
3) Logs:
```bash
docker-compose logs -f
```

## Run from GHCR (prebuilt image)
Pull and run without building locally:
```bash
docker pull ghcr.io/feskolech/telegram2discord:latest
docker run -d --name tg2ds --env-file .env --restart unless-stopped ghcr.io/feskolech/telegram2discord:latest
```

Or use docker‑compose (image is already set in `docker-compose.yml`):
```bash
docker-compose up -d
```

## Configuration (.env)
Minimal:
```
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
TELEGRAM_SOURCE_CHANNEL_ID=-1001234567890
DISCORD_TARGET_CHANNEL_ID=123456789012345678
```

If the channel is **public**, the bot can usually read `username` automatically.
If the channel is **private**, there is no username and the footer will be omitted.
You can set it explicitly:
```
TELEGRAM_SOURCE_CHANNEL_USERNAME=testchannel
```

Multiple channels:
```
CHANNEL_MAP=-1001234567890:123456789012345678,-1002345678901:234567890123456789
CHANNEL_USERNAME_MAP=-1001234567890:testchannel,-1002345678901:otherchannel
```

Retry delays (fixed pauses):
```
RETRY_DELAYS=2,4,8,16,32
```

Embeds (colored text blocks):
```
USE_EMBEDS=1
EMBED_COLOR=0x5865F2
```

## Current behavior
- Only new posts.
- If a post has photos, the bot sends **one** Discord message: attachments + text/footer.
- Video, polls, and other media types are not handled yet.

## Notes
- `ALLOWED_ADMIN_IDS` is reserved for future use.
