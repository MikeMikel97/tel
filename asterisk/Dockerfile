# Asterisk 20 с поддержкой WebRTC и PJSIP
FROM debian:bookworm-slim

# Метаданные
LABEL maintainer="AI Call Agent"
LABEL description="Asterisk 20 with WebRTC, PJSIP, and Russian language support"

# Установка зависимостей
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    # Базовые инструменты
    wget curl gnupg2 ca-certificates \
    # Зависимости для сборки
    build-essential libssl-dev libxml2-dev libncurses5-dev \
    uuid-dev sqlite3 libsqlite3-dev libjansson-dev \
    # PJSIP и WebRTC
    libsrtp2-dev libedit-dev libspeexdsp-dev \
    libcurl4-openssl-dev libgsm1-dev libopus-dev \
    libspeex-dev libvorbis-dev libcodec2-dev \
    # Утилиты
    sox mpg123 git vim procps net-tools iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# Скачивание и сборка Asterisk
WORKDIR /usr/src
RUN wget https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz && \
    tar xzf asterisk-20-current.tar.gz && \
    cd asterisk-20.*/ && \
    # Конфигурация с bundled pjproject и jansson
    ./configure \
        --with-jansson-bundled \
        --with-pjproject-bundled \
        --with-ssl \
        --with-srtp && \
    # Выбор модулей
    make menuselect.makeopts && \
    menuselect/menuselect \
        --enable res_pjsip \
        --enable res_pjsip_session \
        --enable res_pjsip_transport_websocket \
        --enable res_http_websocket \
        --enable chan_pjsip \
        --enable codec_opus \
        --enable res_crypto \
        --enable res_srtp \
        menuselect.makeopts && \
    # Сборка (используем все ядра)
    make -j$(nproc) && \
    make install && \
    make config && \
    ldconfig && \
    # Очистка
    cd / && \
    rm -rf /usr/src/asterisk-20*

# Создание пользователя asterisk
RUN groupadd -r asterisk && \
    useradd -r -g asterisk -d /var/lib/asterisk -s /bin/bash asterisk && \
    chown -R asterisk:asterisk /var/lib/asterisk /var/log/asterisk /var/spool/asterisk /var/run/asterisk /etc/asterisk

# Создание директорий для записей и логов
RUN mkdir -p /var/spool/asterisk/monitor && \
    chown -R asterisk:asterisk /var/spool/asterisk/monitor

# Порты
# 5060/UDP - SIP
# 5061/TCP - SIP TLS
# 8088/TCP - HTTP/WebSocket (ARI, WebRTC)
# 10000-20000/UDP - RTP (медиа)
EXPOSE 5060/udp 5061/tcp 8088/tcp 10000-20000/udp

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD asterisk -rx 'core show version' || exit 1

# Переключение на пользователя asterisk
USER asterisk

# Рабочая директория
WORKDIR /var/lib/asterisk

# Запуск Asterisk в foreground режиме
CMD ["/usr/sbin/asterisk", "-f", "-vvvg", "-c"]
