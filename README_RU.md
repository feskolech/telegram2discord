# tg2ds

Бот‑мост Telegram → Discord (aiogram + discord.py). Переносит **новые** посты из Telegram‑канала в Discord‑канал.

## Что умеет
- Текст + фото (берётся фото максимального размера).
- Альбомы (media group) отправляются **одним** сообщением с несколькими вложениями.
- Текст идёт в embed (цветная полоса слева), если включён `USE_EMBEDS=1`.
- В конец текста добавляется кликабельный футер `@channel | t.me` (если известен username канала).

## Требования
- Docker и docker‑compose на сервере/VPS.
- Telegram‑бот **админ** в исходном канале.
- Discord‑бот добавлен на сервер и имеет права `View Channel`, `Send Messages`, `Attach Files`.

## Как получить токены и ID
### Telegram Bot Token
1) В Telegram откройте @BotFather → `/newbot`.
2) Создайте бота и скопируйте токен.
3) Добавьте бота в канал и сделайте **админом**.

### Telegram Channel ID
Вариант 1 (просто):
1) Перешлите любое сообщение из канала боту @userinfobot.
2) Он пришлёт `ID` канала (обычно начинается с `-100`).

Вариант 2:
1) Перешлите сообщение из канала боту @getmyid_bot.
2) Он покажет `chat_id`.

### Discord Bot Token
1) Откройте Discord Developer Portal → ваше приложение.
2) Раздел **Bot** → `Reset Token` → скопируйте токен.

### Добавить Discord бота на сервер
1) Developer Portal → **OAuth2 → URL Generator**.
2) В Scopes отметьте **bot**.
3) В Bot Permissions отметьте `View Channels`, `Send Messages`, `Attach Files`.
4) Перейдите по сгенерированному URL и добавьте бота на сервер.

### Discord Channel ID
1) В Discord включите **Developer Mode** (User Settings → Advanced).
2) Правый клик по каналу → **Copy ID**.

## Быстрый старт
1) Скопируйте `.env.example` в `.env` и заполните.
2) Запустите:
```bash
docker-compose up -d
```
3) Логи:
```bash
docker-compose logs -f
```

## Запуск из GHCR (готовый образ)
Без локальной сборки:
```bash
docker pull ghcr.io/feskolech/telegram2discord:latest
docker run -d --name tg2ds --env-file .env --restart unless-stopped ghcr.io/feskolech/telegram2discord:latest
```

Или через docker‑compose (образ уже указан в `docker-compose.yml`):
```bash
docker-compose up -d
```

## Настройки (.env)
Минимально:
```
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
TELEGRAM_SOURCE_CHANNEL_ID=-1001234567890
DISCORD_TARGET_CHANNEL_ID=123456789012345678
```

Если канал **публичный**, бот обычно сам получает `username`.
Если канал **приватный**, username нет — футер не появится.
Можно задать явно:
```
TELEGRAM_SOURCE_CHANNEL_USERNAME=testchannel
```

Несколько каналов:
```
CHANNEL_MAP=-1001234567890:123456789012345678,-1002345678901:234567890123456789
CHANNEL_USERNAME_MAP=-1001234567890:testchannel,-1002345678901:otherchannel
```

Повторы при ошибках (фиксированные паузы):
```
RETRY_DELAYS=2,4,8,16,32
```

Embeds (цветные блоки текста):
```
USE_EMBEDS=1
EMBED_COLOR=0x5865F2
```

## Текущее поведение
- Только новые посты.
- Если в посте есть фото, бот отправляет **одно** сообщение в Discord: вложения + текст/футер.
- Видео, опросы и прочие типы пока не обрабатываются.

## Заметки
- `ALLOWED_ADMIN_IDS` пока не используется (зарезервировано на будущее).
