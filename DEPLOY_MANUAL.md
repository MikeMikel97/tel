# 🚀 Ручной Деплой на Сервер

## Шаг 1: Подключись к серверу

```bash
ssh root@46.254.18.120
# Пароль: eTWM7z9PKV
```

## Шаг 2: Выполни эти команды на сервере

### 1️⃣ Обновление системы и установка зависимостей

```bash
apt-get update && apt-get upgrade -y
apt-get install -y curl git apt-transport-https ca-certificates gnupg lsb-release ufw software-properties-common
```

### 2️⃣ Установка Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker
rm get-docker.sh
```

### 3️⃣ Установка Docker Compose

```bash
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### 4️⃣ Клонирование проекта

```bash
cd /opt
git clone https://github.com/MikeMikel97/tel.git telephony
cd /opt/telephony
```

### 5️⃣ Настройка environment

```bash
cp backend/.env.example backend/.env

# Генерация секретного ключа
JWT_SECRET=$(openssl rand -hex 32)

# Обновление конфигурации
sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" backend/.env

# Проверка
cat backend/.env | grep JWT_SECRET_KEY
```

### 6️⃣ Обновление конфигов для работы с IP сервера

```bash
# Обновляем frontend для работы с IP сервера вместо localhost
cd /opt/telephony
sed -i 's/localhost/46.254.18.120/g' frontend/app.js
sed -i 's/localhost/46.254.18.120/g' frontend/webrtc.js

# Проверяем изменения
grep -n "46.254.18.120" frontend/app.js | head -3
```

### 7️⃣ Настройка Firewall

```bash
ufw --force enable
ufw allow 22/tcp           # SSH
ufw allow 80/tcp           # HTTP
ufw allow 443/tcp          # HTTPS
ufw allow 3003/tcp         # Frontend
ufw allow 8000/tcp         # Backend API
ufw allow 5060/udp         # SIP UDP
ufw allow 5060/tcp         # SIP TCP
ufw allow 8088/tcp         # WebRTC WebSocket
ufw allow 10000:10100/udp  # RTP media
ufw reload
ufw status
```

### 8️⃣ Запуск приложения

```bash
cd /opt/telephony
docker-compose down || true
docker-compose up -d --build
```

### 9️⃣ Проверка статуса

```bash
# Подождать 30 секунд
sleep 30

# Проверить статус контейнеров
docker-compose ps

# Проверить логи
docker-compose logs --tail=50
```

---

## ✅ После запуска

### Доступ к интерфейсам:

- **Operator UI:** http://46.254.18.120:3003
- **Admin Panel:** http://46.254.18.120:8000/admin
- **API Docs:** http://46.254.18.120:8000/docs

### Учетные данные:

- **Admin:** `admin` / `D7eva123qwerty`
- **Operator:** `operator` / `operator123`

---

## 🔍 Полезные команды

```bash
# Логи всех сервисов
cd /opt/telephony && docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f asterisk

# Перезапуск
docker-compose restart

# Консоль Asterisk
docker exec -it telephony-asterisk asterisk -rvvv

# Остановка
docker-compose down

# Полная пересборка
docker-compose down && docker-compose up -d --build
```

---

## 🐛 Если что-то не работает

### Проверить порты:
```bash
netstat -tulpn | grep -E '(3003|8000|5060|8088)'
```

### Проверить firewall:
```bash
ufw status verbose
```

### Проверить Docker:
```bash
docker ps
docker stats
```

### Проверить логи ошибок:
```bash
docker-compose logs --tail=100 | grep -i error
```
