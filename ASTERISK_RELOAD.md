# Перезагрузка конфигурации Asterisk

После генерации новых конфигурационных файлов через API (`POST /api/admin/asterisk/generate-config`), необходимо перезагрузить Asterisk для применения изменений.

## Способы перезагрузки

### 1. Через Docker (рекомендуется для локальной разработки)

```bash
docker exec telephony-asterisk asterisk -rx "core reload"
```

### 2. Через Asterisk CLI (если подключены к контейнеру)

```bash
docker exec -it telephony-asterisk asterisk -rvvv
```

Затем в CLI:
```
core reload
```

### 3. Автоматическая перезагрузка через API (требует настройки)

Эндпоинт `/api/admin/asterisk/apply-config` пытается автоматически перезагрузить Asterisk, но требует:
- Docker socket прокинут в backend контейнер
- Docker CLI установлен в backend контейнере

Для production рекомендуется использовать **Asterisk Manager Interface (AMI)** вместо Docker exec.

## Полный цикл обновления конфигурации

1. Внесите изменения через Admin Panel (добавьте компанию, транк, пользователя)
2. Сгенерируйте конфиги: `POST /api/admin/asterisk/generate-config`
3. Перезагрузите Asterisk: `docker exec telephony-asterisk asterisk -rx "core reload"`
4. Проверьте результат: `docker exec telephony-asterisk asterisk -rx "pjsip show endpoints"`

## Скрипт для быстрой перезагрузки

Создайте файл `reload_asterisk.sh`:

```bash
#!/bin/bash
docker exec telephony-asterisk asterisk -rx "core reload"
echo "✅ Asterisk reloaded successfully"
```

Сделайте его исполняемым:
```bash
chmod +x reload_asterisk.sh
```

Используйте:
```bash
./reload_asterisk.sh
```

## Проверка загруженных конфигов

### PJSIP endpoints
```bash
docker exec telephony-asterisk asterisk -rx "pjsip show endpoints"
```

### Dialplan
```bash
docker exec telephony-asterisk asterisk -rx "dialplan show"
```

### SIP registrations
```bash
docker exec telephony-asterisk asterisk -rx "pjsip show registrations"
```
