# AI Call Agent - WebRTC Телефония с AI

Система для обработки звонков с искусственным интеллектом, построенная на Asterisk, FastAPI и WebRTC.

## 🚀 Быстрый старт (Docker)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/MikeMikel97/tel.git
cd tel

# 2. Настроить environment
cp backend/.env.example backend/.env
# Отредактировать backend/.env (указать API ключи если нужны)

# 3. Запустить все сервисы
docker compose up -d

# 4. Проверить статус
docker compose ps
```

**Доступ к интерфейсам:**
- 🎯 **Operator UI:** http://localhost:3003 (логин: `operator`, пароль: `operator123`)
- 🔧 **Admin Panel:** http://localhost:8000/admin (логин: `admin`, пароль: `D7eva123qwerty`)
- 📚 **API Docs:** http://localhost:8000/docs

---

## 📁 Структура проекта

```
Telephony/
├── asterisk/          # Asterisk конфигурация (pjsip, extensions, http)
├── backend/           # FastAPI бэкенд (Python)
│   ├── app/
│   │   ├── api/       # REST API endpoints
│   │   ├── models/    # SQLAlchemy модели (PostgreSQL)
│   │   ├── services/  # Бизнес-логика (AI, Asterisk config)
│   │   └── core/      # Auth, security, deps
│   └── .env           # Environment переменные
├── frontend/          # WebRTC интерфейс оператора (HTML/JS)
└── docker-compose.yml # Orchestration
```

---

## 🔑 Основные возможности

### ✅ Реализовано
- **WebRTC телефон** для операторов (JsSIP + Asterisk)
- **PostgreSQL** для хранения данных (компании, пользователи, звонки)
- **Админ-панель** (SQLAdmin) для управления:
  - Компаниями
  - SIP транками (Mango Office и др.)
  - Телефонными номерами
  - Пользователями (операторы/админы)
  - История звонков
- **Авторизация** для операторов (JWT)
- **История звонков** в UI
- **Динамическая генерация конфигов Asterisk** из БД
- **Исходящие звонки** через UI

### 🔜 Планируется
- Интеграция LLM для анализа разговоров (OpenRouter)
- Speech-to-Text (Soniox API)
- Real-time подсказки операторам
- Расширенная статистика и аналитика

---

## 🗄️ База данных

### Таблицы
- `companies` — клиентские компании
- `users` — операторы и админы
- `sip_trunks` — SIP провайдеры (Mango, Beeline и т.д.)
- `phone_numbers` — телефонные номера
- `call_sessions` — история звонков

### Связи
- `Company` → `SIPTrunk` (1:N)
- `Company` → `PhoneNumber` (1:N)
- `Company` → `User` (1:N)
- `User` → `PhoneNumber` (N:1 current_number)
- `CallSession` → `User` (N:1)

---

## ⚙️ Конфигурация

### Backend (.env)
```env
DATABASE_URL=postgresql+psycopg2://telephony_user:telephony_password_2024@postgres:5432/telephony
JWT_SECRET_KEY=your-secret-key
OPENROUTER_API_KEY=sk-or-v1-...
SONIOX_API_KEY=...
```

### Asterisk
- **Статические конфиги:** `asterisk/pjsip.conf`, `asterisk/extensions.conf`
- **Динамические конфиги:** генерируются backend'ом в `asterisk/dynamic/`
  - Генерация: `POST /api/admin/asterisk/generate-config`
  - Применение: вручную `docker exec telephony-asterisk asterisk -rx "core reload"`

---

## 👤 Управление пользователями

### Создание оператора через админку:
1. Открыть http://localhost:8000/admin
2. Войти (`admin` / `D7eva123qwerty`)
3. Перейти в "Пользователи" → "Create"
4. Заполнить:
   - **Компания ID**: выбрать компанию
   - **Логин**: имя для входа в UI
   - **Пароль для входа в UI**: пароль для localhost:3003
   - **SIP логин**: для регистрации в Asterisk
   - **SIP пароль**: для Asterisk (не для UI!)
   - **Роль**: `operator` или `admin`

**Примечание:** Если пароль не указать, будет использован `operator123` по умолчанию.

---

## 🧪 Тестирование

### Проверка WebRTC
1. Открыть http://localhost:3003
2. Войти (operator/operator123)
3. Нажать "Подключить телефон"
4. Позвонить на `100` (эхо-тест) или `101` (время)

### Проверка API
```bash
# Получить токен
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=operator&password=operator123" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Получить информацию о пользователе
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# История звонков
curl http://localhost:8000/api/calls/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Полезные команды

```bash
# Логи
docker compose logs -f backend
docker compose logs -f asterisk

# Перезапуск сервисов
docker compose restart backend
docker compose restart asterisk

# Консоль Asterisk
docker exec -it telephony-asterisk asterisk -rvvv

# Postgres CLI
docker exec -it telephony-postgres psql -U telephony_user -d telephony

# Полная пересборка
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 📞 Подключение SIP провайдера (Mango Office)

1. Открыть админку → "SIP Транки" → "Create"
2. Заполнить данные от Mango:
   - **Server URI**: `sip:xxxxx@sipdir.mangosip.ru`
   - **Client URI**: `sip:xxxxx@sipdir.mangosip.ru`
   - **Username**: ваш ID
   - **Password**: ваш секрет
3. Сохранить
4. Генерировать конфиги: `POST /api/admin/asterisk/generate-config`
5. Перезагрузить Asterisk: `docker exec telephony-asterisk asterisk -rx "core reload"`

---

## 🚀 Деплой на сервер

1. Установить Docker и Docker Compose
2. Клонировать репозиторий
3. Обновить `.env` с реальными API ключами
4. Настроить Nginx как reverse proxy (SSL + WebSocket)
5. Открыть порты: `5060/udp` (SIP), `10000-10100/udp` (RTP), `80/tcp`, `443/tcp`
6. Запустить: `docker compose up -d`

**Важно:** В production используйте HTTPS и WSS для WebRTC!

---

## 📝 License

MIT

---

## 🤝 Контакты

GitHub: https://github.com/MikeMikel97/tel
