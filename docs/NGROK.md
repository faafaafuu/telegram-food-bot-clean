# Использование ngrok для тестирования Telegram WebApp (HTTPS)

Коротко: Telegram требует HTTPS для WebApp. Для быстрого разработки можно пробросить локальный `web` контейнер через ngrok и подставить публичный `https://` URL в `BASE_URL`.

Требования:
- Установленный `ngrok` в PATH (https://ngrok.com/download)
- `.env` в корне проекта (существует в `./.env`)

Как быстро запустить:

1. Экспортируйте токен (опционально):

```bash
export NGROK_AUTH_TOKEN=your_ngrok_authtoken
```

2. Запустите helper-скрипт (проект ожидается в репо корне):

```bash
./scripts/start_ngrok.sh
```

Скрипт автоматически:
- запускает `ngrok http 8020` (мы предполагаем, что в `docker-compose` nginx проброшен на 8020);
- получает публичный `https://` адрес из локального ngrok API;
- предложит обновить `BASE_URL` в `.env` (создаст `.env.bak`).

3. После обновления `.env` перезапустите сервисы (или только бота), чтобы они взяли новый `BASE_URL`:

```bash
# из каталога проекта
docker compose -f docker/docker-compose.prod.yml up -d --build
# или перезапустить бот контейнер
docker compose -f docker/docker-compose.prod.yml restart bot
```

Примечания:
- Бесплатный ngrok выдаёт временные URL (меняются при перезапуске). Для постоянного URL используйте платный план или настройте Traefik/Let's Encrypt с реальным доменом.
- Если хостовая система уже слушает 80/443, ngrok обходит это ограничение и пробрасывает прямой HTTPS-туннель.
