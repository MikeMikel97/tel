# 🤖 AI Call Agent - Телефонный AI-агент

Система для автоматизации входящих звонков с использованием AI (LLM + Voice-to-Text).

## 🏗️ Архитектура

- **Asterisk 20** - PBX с поддержкой WebRTC и PJSIP
- **Mango Office** - облачная телефония (SIP транк)
- **FastAPI** - backend для AI логики
- **WebRTC** - браузерный телефон оператора
- **OpenRouter** - LLM провайдер
- **Soniox** - распознавание русской речи (V2T)

## 🚀 Быстрый старт

### 1. Предварительные требования

- Docker и Docker Compose
- Минимум 2GB RAM
- Порты 3000, 5060, 8000, 8088 свободны

### 2. Установка

```bash
# Клонируйте репозиторий
git clone <repo-url>
cd Telephony

# Скопируйте и заполните .env файл
cp backend/env.example backend/.env
# Откройте backend/.env и вставьте API ключи:
#   - OPENROUTER_API_KEY
#   - SONIOX_API_KEY

# Запустите систему
./start.sh
```

### 3. Проверка работы

После запуска:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Asterisk CLI: `docker exec -it telephony-asterisk asterisk -rvvv`

## 📋 Конфигурация

### Asterisk

Конфигурационные файлы в `./asterisk/`:
- `pjsip.conf` - основная конфигурация PJSIP
- `pjsip_mango.conf` - настройки Mango Office SIP транка
- `extensions.conf` - диалплан
- `extensions_mango.conf` - обработка входящих от Mango
- `http.conf` - HTTP/WebSocket сервер для WebRTC
- `modules.conf` - загружаемые модули

### Backend

Настройки в `backend/.env`:
```env
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

SONIOX_API_KEY=your_key
SONIOX_MODEL=ru

ASTERISK_ARI_URL=http://asterisk:8088/ari
ASTERISK_ARI_USER=asterisk
ASTERISK_ARI_PASSWORD=asterisk
```

## 🧪 Тестирование

### Тест эхо (локально)
1. Откройте http://localhost:3000
2. Подключитесь как `operator` / `operator123`
3. Позвоните на `100` - услышите эхо

### Тест времени
1. Позвоните на `101` - услышите текущее время

### Тест исходящего звонка через Mango
1. Наберите номер (например, `+79991234567`)
2. Звонок пойдёт через Mango Office SIP транк

## 📊 Мониторинг

### Логи

```bash
# Все сервисы
docker-compose logs -f

# Только Asterisk
docker-compose logs -f asterisk

# Только Backend
docker-compose logs -f backend
```

### Asterisk CLI

```bash
docker exec -it telephony-asterisk asterisk -rvvv

# Полезные команды в CLI:
pjsip show registrations     # Статус регистрации на Mango
pjsip show endpoints          # Список endpoints
pjsip show transports         # WebSocket и UDP транспорты
core show channels            # Активные звонки
module show like pjsip        # PJSIP модули
```

### Health Checks

```bash
# Asterisk
curl http://localhost:8088/ari/asterisk/info

# Backend
curl http://localhost:8000/health
```

## 🐛 Troubleshooting

### Asterisk не регистрируется на Mango

```bash
# Проверьте логи
docker-compose logs asterisk | grep -i mango

# Проверьте статус регистрации
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"

# Проверьте пароль в asterisk/pjsip_mango.conf
```

### WebRTC не подключается

```bash
# Проверьте что порт 8088 открыт
netstat -an | grep 8088

# Проверьте WebSocket транспорт
docker exec telephony-asterisk asterisk -rx "pjsip show transports"

# Убедитесь что SSL сертификаты созданы
ls -la asterisk/keys/asterisk.pem
```

### PJSIP модули не загружаются

```bash
# Проверьте загрузку модулей
docker exec telephony-asterisk asterisk -rx "module show like pjsip"

# Перезапустите Asterisk
docker-compose restart asterisk

# Если не помогает - пересоберите образ
docker-compose build --no-cache asterisk
docker-compose up -d asterisk
```

## 🔧 Разработка

### Горячая перезагрузка Backend

Backend запущен с `--reload`, изменения в `./backend/` применяются автоматически.

### Обновление конфигурации Asterisk

```bash
# Отредактируйте файлы в ./asterisk/
# Перезагрузите конфигурацию без перезапуска:
docker exec telephony-asterisk asterisk -rx "pjsip reload"
docker exec telephony-asterisk asterisk -rx "dialplan reload"
```

### Доступ к записям разговоров

```bash
# Записи сохраняются в Docker volume
docker volume inspect telephony_asterisk-recordings

# Копирование записи на хост
docker cp telephony-asterisk:/var/spool/asterisk/monitor/ ./recordings/
```

## 📦 Деплой на продакшн

### На сервер с Docker

```bash
# 1. Скопируйте проект на сервер
scp -r . user@server:/opt/telephony

# 2. На сервере запустите
cd /opt/telephony
./start.sh

# 3. Обновите внешние IP в pjsip.conf
# external_media_address=ВАШ_IP
# external_signaling_address=ВАШ_IP
```

### Важно для продакшна

1. **Firewall**: Откройте порты
   - 5060/UDP - SIP
   - 8088/TCP - WebSocket
   - 10000-20000/UDP - RTP (медиа)

2. **SSL**: Используйте Let's Encrypt для WebRTC
   ```bash
   certbot certonly --standalone -d yourdomain.com
   # Скопируйте сертификаты в ./asterisk/keys/
   ```

3. **Безопасность**: Смените пароли в конфигах
   - `asterisk/pjsip.conf` - WebRTC оператор
   - `asterisk/pjsip_mango.conf` - Mango Office

4. **Мониторинг**: Настройте мониторинг контейнеров

## 📚 Дополнительная документация

- [ARCHITECTURE.md](ARCHITECTURE.md) - подробная архитектура
- [NEXT_STEPS.md](NEXT_STEPS.md) - план развития

## 📝 Лицензия

MIT
