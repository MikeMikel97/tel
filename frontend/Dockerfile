FROM nginx:alpine

# Копирование файлов frontend
COPY . /usr/share/nginx/html/

# Порт
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
