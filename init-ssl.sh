#!/bin/bash

# Скрипт для первоначальной настройки SSL сертификатов
# Запускать на сервере после настройки DNS

set -e

DOMAIN="calls4ai.ru"
EMAIL="admin@calls4ai.ru"  # Укажи свой email

echo "🔐 Настройка SSL для домена $DOMAIN"

# Создаем директории
mkdir -p certbot/conf certbot/www

# Проверяем DNS
echo "📡 Проверка DNS записи..."
RESOLVED_IP=$(dig +short $DOMAIN | tail -n1)
if [ -z "$RESOLVED_IP" ]; then
    echo "❌ Домен $DOMAIN не резолвится!"
    echo "   Настрой A-запись в DNS панели:"
    echo "   Тип: A"
    echo "   Имя: @"
    echo "   Значение: 46.254.18.120"
    exit 1
fi

echo "✅ Домен резолвится в: $RESOLVED_IP"

# Временно запускаем Nginx без SSL
echo "📦 Запуск Nginx для проверки Let's Encrypt..."
docker-compose up -d nginx-proxy

# Ждем запуска
sleep 5

# Получаем сертификат
echo "🔑 Получение SSL сертификата от Let's Encrypt..."
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL сертификат получен успешно!"
    echo "📁 Сертификаты сохранены в: ./certbot/conf/live/$DOMAIN/"
    
    # Перезапускаем Nginx с SSL
    echo "🔄 Перезапуск Nginx с SSL..."
    docker-compose restart nginx-proxy
    
    echo ""
    echo "🎉 ГОТОВО! Сайт доступен по адресу:"
    echo "   https://$DOMAIN"
    echo "   https://www.$DOMAIN"
    echo ""
    echo "🔧 Admin Panel: https://$DOMAIN/admin"
    echo "📚 API Docs: https://$DOMAIN/docs"
    echo "📞 Operator UI: https://$DOMAIN"
else
    echo "❌ Ошибка получения сертификата!"
    echo "   Убедись что:"
    echo "   1. DNS настроен правильно"
    echo "   2. Порты 80 и 443 открыты"
    echo "   3. Домен указывает на этот сервер"
    exit 1
fi
