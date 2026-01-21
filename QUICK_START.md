# ⚡ Быстрый старт за 5 минут

## 📋 Что нужно перед началом

1. ✅ Docker установлен
2. ✅ API ключи:
   - OpenRouter API key
   - Soniox API key

## 🚀 3 простых шага

### Шаг 1: Настройка API ключей

```bash
# Скопируйте и откройте файл
cp backend/env.example backend/.env
nano backend/.env

# Вставьте ваши ключи:
# OPENROUTER_API_KEY=sk-or-v1-...
# SONIOX_API_KEY=...
```

### Шаг 2: Запуск

```bash
./start.sh
```

Скрипт автоматически:
- ✅ Сгенерирует SSL сертификаты для WebRTC
- ✅ Соберёт Docker образы
- ✅ Запустит Asterisk, Backend, Frontend
- ✅ Проверит подключение к Mango Office

### Шаг 3: Проверка

Откройте в браузере: **http://localhost:3000**

## 🎯 Что дальше?

### Тест локального эхо

1. На странице http://localhost:3000 нажмите "Connect"
2. Введите:
   - Username: `operator`
   - Password: `operator123`
3. Позвоните на `100` - услышите эхо

### Проверка Mango Office

```bash
# Открыть Asterisk CLI
docker exec -it telephony-asterisk asterisk -rvvv

# В CLI выполнить:
pjsip show registrations
```

Должно быть:
```
mango-registration/operator1@aiagent.mangosip.ru   Registered
```

## 🐛 Что-то не работает?

### PJSIP модули не загрузились

```bash
# Проверьте
docker exec telephony-asterisk asterisk -rx "module show like pjsip"

# Если пусто - пересоберите образ
docker-compose down
docker-compose build --no-cache asterisk
docker-compose up -d
```

### Mango не регистрируется

```bash
# Проверьте пароль в asterisk/pjsip_mango.conf
cat asterisk/pjsip_mango.conf | grep password

# Проверьте логи
docker-compose logs asterisk | grep -i mango
```

### WebRTC не подключается

```bash
# Проверьте сертификаты
ls -la asterisk/keys/asterisk.pem

# Проверьте WebSocket порт
netstat -an | grep 8088

# Проверьте браузер консоль (F12)
```

## 📊 Полезные команды

```bash
# Логи всех сервисов
docker-compose logs -f

# Asterisk CLI (интерактивный режим)
docker exec -it telephony-asterisk asterisk -rvvv

# Остановить всё
docker-compose down

# Перезапустить Asterisk
docker-compose restart asterisk

# Пересобрать образы
docker-compose build
```

## 🎉 Готово!

Теперь у вас работает:
- ✅ Asterisk с PJSIP и WebRTC
- ✅ Подключение к Mango Office
- ✅ Браузерный WebRTC телефон
- ✅ Backend для AI логики
- ✅ Frontend интерфейс

## 🚢 Деплой на сервер

Когда всё протестировано локально:

```bash
# Создайте архив
tar czf deploy.tar.gz \
  docker-compose.yml \
  asterisk/ \
  backend/ \
  frontend/ \
  start.sh

# Скопируйте на сервер
scp deploy.tar.gz root@your-server:/opt/

# На сервере
cd /opt
tar xzf deploy.tar.gz
./start.sh
```

Подробнее: [DEPLOY.md](DEPLOY.md)

## 📚 Документация

- [README.md](README.md) - полная документация
- [ARCHITECTURE.md](ARCHITECTURE.md) - архитектура системы
- [DEPLOY.md](DEPLOY.md) - деплой на продакшн

## 💬 Нужна помощь?

Проверьте логи:
```bash
docker-compose logs -f asterisk
```

Откройте Issue на GitHub или напишите в поддержку.
