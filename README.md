# Otus-HW-counter-service — сервис счётчиков непрочитанных сообщений

Сервис хранит счётчики непрочитанных сообщений по диалогам. Рассчитан на **большую нагрузку на чтение**: счётчики лежат в Redis, чтение — один `HGETALL`/`HGET`.

Консистентность с реальным числом сообщений обеспечивается паттерном **choreography SAGA**: события диалогов (`message.sent`, `dialog.read`) публикуются chat-service'ом в Kafka, а этот сервис их потребляет и обновляет счётчики (eventual consistency).

**Отчёт по архитектуре:** [docs/REVIEW.md](docs/REVIEW.md)

---

## Место в системе

| Репозиторий | Роль |
|-------------|------|
| [Otus-HW_01](https://github.com/kapkaevandrey/Otus-HW_01) | монолит соцсети, прокси диалогов |
| [Otus-HW-chats](https://github.com/kapkaevandrey/Otus-HW-chats) | диалоги, Redis outbox, relay → Kafka |
| **Otus-HW-counter-service** (этот репозиторий) | consumer Kafka, счётчики непрочитанных в Redis, API чтения |

```
chat-service ──(outbox)──► Kafka topic: social.dialog.messages ──► counter-service ──► Redis (unread:{user})
                                                                          │
                                                        GET /api/v1/counters/{user}/unread ◄── клиент
```

---

## Стек

- Python 3.14, FastAPI, uvicorn
- aiokafka (consumer)
- Redis / Valkey (хранилище счётчиков + идемпотентность, атомарность через Lua)

---

## Быстрый запуск (Docker Compose)

Поднимает сервис + Redis (Valkey) + Kafka + Kafka UI:

```bash
docker compose up -d --build
```

| Компонент | Адрес |
|-----------|-------|
| API сервиса | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Kafka | localhost:9092 |
| Kafka UI | http://localhost:8082 |
| Redis (Valkey) | localhost:6379 |

Проверка:

```bash
curl http://localhost:8000/healthz   # OK
```

Остановка:

```bash
docker compose down
```

---

## API

| Метод | Путь | Ответ |
|-------|------|-------|
| `GET` | `/api/v1/counters/{user_id}/unread` | `{user_id, total, by_peer: [{peer_id, count}]}` |
| `GET` | `/api/v1/counters/{user_id}/unread/total` | число — суммарное количество непрочитанных |
| `GET` | `/healthz` | проба готовности |

Пример:

```bash
USER_ID=00000000-0000-0000-0000-000000000001
curl "http://localhost:8000/api/v1/counters/$USER_ID/unread"
```

```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "total": 3,
  "by_peer": [
    {"peer_id": "00000000-0000-0000-0000-0000000000aa", "count": 3}
  ]
}
```

---

## Как проверить, что счётчик меняется

### Вариант A. Полный E2E (chat-service публикует события)

Запустить chat-service (см. его README), отправить сообщение через его API — chat-service опубликует `message.sent` в Kafka, этот сервис увеличит счётчик. Открытие диалога (`GET .../list`) публикует `dialog.read` → счётчик обнуляется.

> Kafka одна на всю систему. Если запущен монолит/chat со своей Kafka на `localhost:9092`, у этого сервиса свою Kafka не поднимать, а указать `KAFKA_BROKERS=localhost:9092`.

### Вариант B. Вручную через Kafka UI

Открыть http://localhost:8082 → топик `social.dialog.messages` → **Produce Message**. Тело `message.sent` (увеличит `unread:{recipient_id}[sender_id]`):

```json
{
  "event_id": "11111111-1111-1111-1111-111111111111",
  "type": "message.sent",
  "recipient_id": "00000000-0000-0000-0000-000000000001",
  "sender_id": "00000000-0000-0000-0000-0000000000aa",
  "conversation_id": "00000000-0000-0000-0000-0000000000cc",
  "message_id": "00000000-0000-0000-0000-0000000000dd",
  "sent_at": "2026-07-10T10:00:00Z"
}
```

Тело `dialog.read` (обнулит `unread:{user_id}[peer_id]`):

```json
{
  "event_id": "22222222-2222-2222-2222-222222222222",
  "type": "dialog.read",
  "user_id": "00000000-0000-0000-0000-000000000001",
  "peer_id": "00000000-0000-0000-0000-0000000000aa",
  "conversation_id": "00000000-0000-0000-0000-0000000000cc",
  "read_at": "2026-07-10T10:05:00Z"
}
```

После продюса — снова дёрнуть `GET /api/v1/counters/{user_id}/unread`.

---

## Локальная разработка

```bash
make install          # uv sync --group dev
uv run uvicorn app.server:app --port 8000
```

Тесты и проверки (нужен запущенный Redis на localhost:6379):

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```
