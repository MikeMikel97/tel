#!/bin/bash

# ============================================
# AI Call Agent - Startup Script
# ============================================

set -e

echo "🚀 Starting AI Call Agent..."

# Проверка наличия .env файла
if [ ! -f "./backend/.env" ]; then
    echo "⚠️  Создаю .env файл из примера..."
    cp ./backend/env.example ./backend/.env
    echo "✅ Файл ./backend/.env создан. Пожалуйста, заполните API ключи!"
    echo ""
    echo "Необходимо заполнить:"
    echo "  - OPENROUTER_API_KEY"
    echo "  - SONIOX_API_KEY"
    echo ""
    read -p "Нажмите Enter после заполнения .env файла..."
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker проверен"

# Генерация SSL сертификатов для DTLS (WebRTC)
if [ ! -f "./asterisk/keys/asterisk.pem" ]; then
    echo "🔐 Генерирую SSL сертификаты для WebRTC..."
    mkdir -p ./asterisk/keys
    openssl req -x509 -newkey rsa:4096 -keyout ./asterisk/keys/asterisk.key \
        -out ./asterisk/keys/asterisk.crt -days 365 -nodes \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=AICallAgent/CN=localhost"
    cat ./asterisk/keys/asterisk.crt ./asterisk/keys/asterisk.key > ./asterisk/keys/asterisk.pem
    echo "✅ Сертификаты созданы"
fi

# Остановка старых контейнеров
echo "🛑 Останавливаю старые контейнеры..."
docker-compose down 2>/dev/null || true

# Сборка и запуск
echo "🔨 Собираю Docker образы..."
docker-compose build

echo "▶️  Запускаю сервисы..."
docker-compose up -d

# Ожидание готовности Asterisk
echo "⏳ Ожидание запуска Asterisk..."
for i in {1..30}; do
    if docker exec telephony-asterisk asterisk -rx "core show version" &>/dev/null; then
        echo "✅ Asterisk запущен!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Asterisk не запустился за 30 секунд"
        docker-compose logs asterisk
        exit 1
    fi
    sleep 1
done

# Проверка модулей PJSIP
echo "🔍 Проверка модулей PJSIP..."
docker exec telephony-asterisk asterisk -rx "module show like pjsip" | head -5

# Проверка транспортов
echo "🔍 Проверка PJSIP транспортов..."
docker exec telephony-asterisk asterisk -rx "pjsip show transports"

# Проверка регистрации Mango
echo "🔍 Проверка регистрации на Mango Office..."
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"

echo ""
echo "✅ AI Call Agent запущен!"
echo ""
echo "📊 Доступные сервисы:"
echo "  - Frontend:  http://localhost:3000"
echo "  - Backend:   http://localhost:8000"
echo "  - Asterisk WebSocket: ws://localhost:8088/ws"
echo ""
echo "📝 Полезные команды:"
echo "  docker-compose logs -f asterisk    # Логи Asterisk"
echo "  docker-compose logs -f backend     # Логи Backend"
echo "  docker exec -it telephony-asterisk asterisk -rvvv  # Asterisk CLI"
echo "  docker-compose down                # Остановить все"
echo "  docker-compose restart asterisk    # Перезапустить Asterisk"
echo ""
