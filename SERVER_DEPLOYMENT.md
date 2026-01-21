# 🚀 Развертывание на сервере

## Подготовка сервера

### Требования
- Ubuntu 20.04+ / Debian 11+
- Docker & Docker Compose
- Минимум 2GB RAM
- 20GB свободного места

### Установка Docker

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверяем установку
docker --version
docker-compose --version
```

## Загрузка проекта

```bash
# Клонируем репозиторий
git clone https://github.com/MikeMikel97/tel.git
cd tel

# Создаем .env файл для backend
cp backend/env.example backend/.env
```

## Настройка переменных окружения

Отредактируйте `backend/.env`:

```bash
nano backend/.env
```

**Важные параметры для production:**

```ini
# Database
DATABASE_URL=postgresql://telephony_user:YOUR_STRONG_PASSWORD@postgres:5432/telephony

# OpenRouter API (для LLM)
OPENROUTER_API_KEY=your-openrouter-api-key

# Soniox API (для STT на русском)
SONIOX_API_KEY=your-soniox-api-key

# JWT
JWT_SECRET_KEY=generate-strong-random-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Asterisk ARI
ASTERISK_HOST=asterisk
ASTERISK_ARI_PORT=8088
ASTERISK_ARI_USER=ai-agent
ASTERISK_ARI_PASSWORD=generate-strong-password-here

# Debug mode (отключить в production)
DEBUG=false
```

## Настройка Mango Office SIP

Отредактируйте `asterisk/pjsip_mango.conf`:

```bash
nano asterisk/pjsip_mango.conf
```

Обновите данные вашего транка:
- `username` - ваш логин от Mango Office
- `password` - ваш пароль от Mango Office
- `server_uri` - адрес сервера Mango
- `realm` - домен Mango

## Запуск системы

```bash
# Запускаем все сервисы
docker-compose up -d

# Проверяем статус
docker-compose ps

# Смотрим логи (если нужно)
docker-compose logs -f
```

## Применение миграций БД

```bash
# Выполняем миграции Alembic
docker-compose exec backend alembic upgrade head

# Создаем тестовых пользователей (опционально)
docker-compose exec backend python create_test_data.py
```

## Создание первого пользователя через API

```bash
# Получаем токен админа (если создали через create_test_data.py)
TOKEN=$(curl -s -X POST http://YOUR_SERVER_IP:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Создаем нового оператора через админку
# Или используйте веб-интерфейс: http://YOUR_SERVER_IP:8000/admin
```

## URL доступа к системе

После развертывания система будет доступна по следующим адресам:

### С использованием IP адреса:

- **UI Операторов:** `http://YOUR_SERVER_IP:3003`
- **Админ-панель:** `http://YOUR_SERVER_IP:8000/admin`
  - Username: `admin`
  - Password: `D7eva123qwerty`
- **API документация:** `http://YOUR_SERVER_IP:8000/docs`
- **Backend API:** `http://YOUR_SERVER_IP:8000/api`

### С использованием домена (рекомендуется):

Настройте Nginx reverse proxy для:
- `https://yourdomain.com` → frontend (port 3003)
- `https://yourdomain.com/api` → backend (port 8000)
- `https://yourdomain.com/admin` → admin panel (port 8000)

## Настройка Nginx Reverse Proxy (опционально)

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

Создайте конфиг `/etc/nginx/sites-available/telephony`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Admin Panel
    location /admin {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Asterisk WebSocket
    location /asterisk/ws {
        proxy_pass http://localhost:8088;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Активируйте конфиг:

```bash
sudo ln -s /etc/nginx/sites-available/telephony /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Установите SSL сертификат:

```bash
sudo certbot --nginx -d yourdomain.com
```

## Обновление конфигурации Asterisk

После добавления компаний/транков/пользователей через админ-панель:

```bash
# Генерируем конфиги из БД
curl -X POST http://localhost:8000/api/admin/asterisk/generate-config \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Перезагружаем Asterisk
docker exec telephony-asterisk asterisk -rx "core reload"
```

## Мониторинг и логи

```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f asterisk

# Asterisk CLI
docker exec -it telephony-asterisk asterisk -rvvv

# Статус PJSIP endpoints
docker exec telephony-asterisk asterisk -rx "pjsip show endpoints"

# Статус SIP регистраций
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"
```

## Firewall настройки

```bash
# Открываем необходимые порты
sudo ufw allow 80/tcp    # HTTP (Nginx)
sudo ufw allow 443/tcp   # HTTPS (Nginx)
sudo ufw allow 3003/tcp  # Frontend (если без Nginx)
sudo ufw allow 8000/tcp  # Backend API (если без Nginx)
sudo ufw allow 5060/udp  # SIP
sudo ufw allow 5060/tcp  # SIP over TCP
sudo ufw allow 10000:10100/udp  # RTP

sudo ufw enable
sudo ufw status
```

## Backup

```bash
# Backup базы данных
docker-compose exec postgres pg_dump -U telephony_user telephony > backup_$(date +%Y%m%d).sql

# Backup volume с записями звонков
docker run --rm -v telephony_asterisk-recordings:/data -v $(pwd):/backup ubuntu tar czf /backup/recordings_$(date +%Y%m%d).tar.gz /data
```

## Обновление системы

```bash
# Останавливаем сервисы
docker-compose down

# Получаем последние изменения
git pull

# Пересобираем образы
docker-compose build

# Запускаем
docker-compose up -d

# Применяем миграции (если есть)
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Проблема: Backend не запускается

```bash
# Проверьте логи
docker-compose logs backend

# Проверьте .env файл
docker-compose exec backend cat .env
```

### Проблема: Asterisk не может зарегистрироваться на SIP провайдере

```bash
# Проверьте PJSIP конфиг
docker exec telephony-asterisk cat /etc/asterisk/pjsip_mango.conf

# Проверьте регистрации
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"

# Проверьте логи
docker logs telephony-asterisk
```

### Проблема: WebRTC не работает

1. Проверьте что STUN сервер доступен
2. Убедитесь что порты 10000-10100/udp открыты
3. Проверьте WebSocket соединение в браузере (DevTools → Network → WS)

## Производительность

Для production рекомендуется:
- Минимум 4GB RAM для комфортной работы
- SSD диск
- Настроить логротацию:

```bash
# Добавьте в /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Безопасность

1. **Смените все пароли по умолчанию** в:
   - `backend/.env` (JWT_SECRET_KEY, DATABASE_URL, ASTERISK_ARI_PASSWORD)
   - `backend/app/admin_auth.py` (ADMIN_USERNAME и ADMIN_PASSWORD)
   - Админ-панель (создайте нового админа и удалите дефолтного)

2. **Используйте HTTPS** (Nginx + Let's Encrypt)

3. **Ограничьте доступ к портам** (firewall)

4. **Регулярно обновляйте** систему и Docker образы

5. **Настройте backup** базы данных и записей

---

## Контакты и поддержка

Если возникли вопросы или проблемы при развертывании, обращайтесь к администратору системы.
