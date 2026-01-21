# 🚀 Деплой на продакшн сервер

## Вариант 1: Быстрый деплой с локального Docker setup

### На локальной машине

```bash
# 1. Убедитесь что все работает локально
./start.sh

# 2. Проверьте что всё ОК
docker-compose ps
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"

# 3. Создайте архив проекта
tar czf telephony-deploy.tar.gz \
  docker-compose.yml \
  asterisk/ \
  backend/ \
  frontend/ \
  start.sh \
  README.md

# 4. Скопируйте на сервер
scp telephony-deploy.tar.gz root@46.254.18.120:/root/
```

### На сервере

```bash
# 1. Подключитесь к серверу
ssh root@46.254.18.120

# 2. Распакуйте проект
cd /opt
mkdir -p telephony
cd telephony
tar xzf /root/telephony-deploy.tar.gz

# 3. Обновите внешний IP в конфигах
sed -i 's/0.0.0.0/46.254.18.120/g' asterisk/pjsip.conf

# 4. Создайте .env файл
cp backend/env.example backend/.env
nano backend/.env  # Вставьте API ключи

# 5. Запустите
chmod +x start.sh
./start.sh
```

## Вариант 2: Миграция с существующего сервера

### Если на сервере уже есть Asterisk

```bash
# 1. Остановите старый Asterisk
systemctl stop asterisk

# 2. Сделайте бэкап старых конфигов
mkdir -p /root/asterisk-backup
cp -r /etc/asterisk/* /root/asterisk-backup/

# 3. Установите Docker (если нет)
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 4. Разверните новый стек
cd /opt/telephony
./start.sh

# 5. Проверьте регистрацию
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"
```

## Настройка firewall

```bash
# UFW
ufw allow 5060/udp comment 'SIP'
ufw allow 8088/tcp comment 'WebSocket'
ufw allow 10000:20000/udp comment 'RTP'
ufw allow 3000/tcp comment 'Frontend'
ufw allow 8000/tcp comment 'Backend API'

# iptables
iptables -A INPUT -p udp --dport 5060 -j ACCEPT
iptables -A INPUT -p tcp --dport 8088 -j ACCEPT
iptables -A INPUT -p udp --dport 10000:20000 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables-save > /etc/iptables/rules.v4
```

## Настройка systemd для автозапуска

```bash
# Создайте systemd service
cat > /etc/systemd/system/telephony.service <<EOF
[Unit]
Description=AI Call Agent Telephony Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/telephony
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Включите автозапуск
systemctl daemon-reload
systemctl enable telephony
systemctl start telephony
```

## Мониторинг

```bash
# Логи в реальном времени
docker-compose logs -f

# Проверка состояния
docker-compose ps
docker stats

# Asterisk CLI
docker exec -it telephony-asterisk asterisk -rvvv

# Проверка регистрации Mango
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"

# Проверка активных звонков
docker exec telephony-asterisk asterisk -rx "core show channels"
```

## Обновление

```bash
# На локальной машине
git pull
docker-compose build
tar czf telephony-update.tar.gz docker-compose.yml asterisk/ backend/ frontend/
scp telephony-update.tar.gz root@46.254.18.120:/root/

# На сервере
cd /opt/telephony
docker-compose down
tar xzf /root/telephony-update.tar.gz
docker-compose up -d --build
```

## Откат на старую версию

```bash
# Если новая версия не работает
cd /opt/telephony
docker-compose down

# Восстановите бэкап
cp -r /root/asterisk-backup/* /etc/asterisk/

# Запустите старый Asterisk
systemctl start asterisk
```

## Проблемы и решения

### Docker not found

```bash
curl -fsSL https://get.docker.com | sh
```

### Permission denied

```bash
usermod -aG docker $USER
newgrp docker
```

### Port already in use

```bash
# Найдите процесс занимающий порт
netstat -tulpn | grep :5060

# Остановите старый Asterisk
systemctl stop asterisk
killall -9 asterisk
```

### PJSIP modules not loading

```bash
# Пересоберите образ без кэша
docker-compose build --no-cache asterisk
docker-compose up -d asterisk
```

## Безопасность

1. **Смените пароли** в `asterisk/pjsip.conf` и `asterisk/pjsip_mango.conf`
2. **Используйте SSL** для WebRTC (Let's Encrypt)
3. **Ограничьте доступ** к портам через firewall
4. **Регулярные бэкапы** конфигов и записей
5. **Мониторинг** логов на подозрительную активность

## SSL сертификаты для WebRTC

```bash
# Установите certbot
apt-get install certbot

# Получите сертификат
certbot certonly --standalone -d yourdomain.com

# Скопируйте в проект
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem asterisk/keys/asterisk.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem asterisk/keys/asterisk.key
cat asterisk/keys/asterisk.crt asterisk/keys/asterisk.key > asterisk/keys/asterisk.pem

# Перезапустите Asterisk
docker-compose restart asterisk
```

## Резервное копирование

```bash
# Скрипт бэкапа
cat > /root/backup-telephony.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/root/telephony-backups"
mkdir -p $BACKUP_DIR

# Бэкап конфигов
tar czf $BACKUP_DIR/config-$DATE.tar.gz /opt/telephony/asterisk/ /opt/telephony/backend/.env

# Бэкап записей (последние 7 дней)
docker exec telephony-asterisk tar czf /tmp/recordings-$DATE.tar.gz \
  --mtime=-7 /var/spool/asterisk/monitor/
docker cp telephony-asterisk:/tmp/recordings-$DATE.tar.gz $BACKUP_DIR/

# Удаление старых бэкапов (>30 дней)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup-telephony.sh

# Добавьте в cron (каждый день в 3:00)
echo "0 3 * * * /root/backup-telephony.sh" | crontab -
```
