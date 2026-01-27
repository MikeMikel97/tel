# 🚀 Production Deployment Guide

## Быстрый деплой на чистый сервер

### Требования:
- Ubuntu 20.04+ / Debian 11+
- Root доступ
- Домен с A-записями на IP сервера
- Минимум 2GB RAM, 20GB disk

---

## 📋 Шаг 1: Настройка DNS

Перед деплоем настрой DNS записи:

```
Type: A
Name: calls4ai.ru
Value: 46.254.18.120

Type: A
Name: www.calls4ai.ru
Value: 46.254.18.120
```

Проверь что DNS применился:
```bash
dig calls4ai.ru +short
# Должен вернуть IP сервера
```

---

## 🔧 Шаг 2: Автоматический деплой

Подключись к серверу:
```bash
ssh root@46.254.18.120
```

Скачай и запусти скрипт деплоя:
```bash
curl -fsSL https://raw.githubusercontent.com/MikeMikel97/tel/main/deploy-fresh-server.sh -o deploy.sh
chmod +x deploy.sh
./deploy.sh calls4ai.ru admin@calls4ai.ru
```

Скрипт автоматически:
1. ✅ Установит Docker и Docker Compose
2. ✅ Склонирует репозиторий
3. ✅ Настроит окружение
4. ✅ Запустит базу данных и миграции
5. ✅ Получит SSL сертификат от Let's Encrypt
6. ✅ Запустит все сервисы с HTTPS

---

## 🎯 Шаг 3: Проверка

После деплоя проверь:

```bash
# Статус контейнеров
cd /opt/telephony
docker-compose -f docker-compose.prod.yml ps

# Проверка HTTPS
curl -I https://calls4ai.ru
```

---

## 🔑 Учетные данные

### Admin Panel
URL: https://calls4ai.ru/admin
- **Логин:** `admin`
- **Пароль:** `D7eva123qwerty`

### Operator UI
URL: https://calls4ai.ru
- **Тестовый оператор:** `testuser` / `Test123!`
- **SIP:** `testoperator` / `Test123!`

### API Documentation
URL: https://calls4ai.ru/docs

---

## 🔄 Управление

### Перезапуск сервисов
```bash
cd /opt/telephony
docker-compose -f docker-compose.prod.yml restart
```

### Просмотр логов
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Только backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Только asterisk
docker-compose -f docker-compose.prod.yml logs -f asterisk
```

### Обновление кода
```bash
cd /opt/telephony
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### Остановка всех сервисов
```bash
docker-compose -f docker-compose.prod.yml down
```

### Полная очистка (включая данные)
```bash
docker-compose -f docker-compose.prod.yml down -v
```

---

## 🛠️ Ручной деплой (если нужен контроль)

### 1. Установка Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Установка Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Клонирование репозитория
```bash
cd /opt
git clone https://github.com/MikeMikel97/tel.git telephony
cd telephony
```

### 4. Настройка окружения
```bash
# .env уже в репозитории с правильными ключами
# Но можно сгенерировать новый JWT secret:
JWT_SECRET=$(openssl rand -hex 32)
sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" backend/.env
```

### 5. Запуск базовых сервисов
```bash
docker-compose -f docker-compose.prod.yml up -d postgres asterisk backend frontend
sleep 30
```

### 6. Миграции и тестовые данные
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker-compose -f docker-compose.prod.yml exec backend python create_test_data.py
```

### 7. Получение SSL сертификата
```bash
# Временный nginx для Certbot
docker run -d --name temp-nginx -p 80:80 \
  -v $(pwd)/certbot/www:/var/www/certbot:ro \
  nginx:alpine

# Получаем сертификат
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@calls4ai.ru \
  --agree-tos --no-eff-email \
  -d calls4ai.ru -d www.calls4ai.ru

# Останавливаем временный nginx
docker stop temp-nginx && docker rm temp-nginx
```

### 8. Запуск с SSL
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔐 SSL Certificate Renewal

Certbot автоматически обновляет сертификат каждые 12 часов.

Проверить статус:
```bash
docker-compose -f docker-compose.prod.yml exec certbot certbot certificates
```

Ручное обновление:
```bash
docker-compose -f docker-compose.prod.yml exec certbot certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## 🐛 Troubleshooting

### Проблема: "Failed to connect"
```bash
# Проверь DNS
dig calls4ai.ru +short

# Проверь firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Проблема: "502 Bad Gateway"
```bash
# Проверь статус backend
docker-compose -f docker-compose.prod.yml logs backend

# Перезапусти backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Проблема: "Database connection failed"
```bash
# Проверь PostgreSQL
docker-compose -f docker-compose.prod.yml logs postgres

# Перезапусти postgres
docker-compose -f docker-compose.prod.yml restart postgres
```

### Проверка места на диске
```bash
df -h
docker system df
```

### Очистка места
```bash
# Удаление неиспользуемых образов
docker system prune -a

# Очистка логов (они ограничены 10MB × 3 файла)
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

---

## 📊 Мониторинг

### Статус всех контейнеров
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Использование ресурсов
```bash
docker stats
```

### Проверка здоровья
```bash
curl https://calls4ai.ru/api/health
```

---

## 🔄 Бэкапы

### База данных
```bash
# Создать backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U telephony_user telephony > backup_$(date +%Y%m%d).sql

# Восстановить из backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U telephony_user telephony < backup_20240127.sql
```

### Конфигурация Asterisk
```bash
# Backup динамических конфигов
docker cp telephony-asterisk:/etc/asterisk/dynamic ./asterisk-backup/
```

---

## 📞 Поддержка

Если что-то не работает:
1. Проверь логи: `docker-compose -f docker-compose.prod.yml logs`
2. Проверь статус: `docker-compose -f docker-compose.prod.yml ps`
3. Перезапусти: `docker-compose -f docker-compose.prod.yml restart`
