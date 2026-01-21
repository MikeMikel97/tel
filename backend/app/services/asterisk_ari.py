"""Интеграция с Asterisk ARI"""
import asyncio
import aiohttp
from typing import Callable, Optional
from loguru import logger
from ..config import get_settings

settings = get_settings()


class AsteriskARIService:
    """Сервис для работы с Asterisk через ARI"""
    
    def __init__(self):
        self.base_url = f"http://{settings.asterisk_host}:{settings.asterisk_ari_port}/ari"
        self.ws_url = f"ws://{settings.asterisk_host}:{settings.asterisk_ari_port}/ari/events"
        self.auth = aiohttp.BasicAuth(
            settings.asterisk_ari_user,
            settings.asterisk_ari_password
        )
        self.app_name = "ai-agent"
        self.event_handlers: dict[str, list[Callable]] = {}
        self._ws_task: Optional[asyncio.Task] = None
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Выполняет HTTP запрос к ARI"""
        async with aiohttp.ClientSession(auth=self.auth) as session:
            url = f"{self.base_url}/{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"ARI error: {response.status} - {text}")
                    return {}
    
    async def get_channels(self) -> list:
        """Получает список активных каналов"""
        return await self._make_request("GET", "channels")
    
    async def get_channel(self, channel_id: str) -> dict:
        """Получает информацию о канале"""
        return await self._make_request("GET", f"channels/{channel_id}")
    
    async def snoop_channel(
        self, 
        channel_id: str, 
        spy: str = "both",  # in, out, both
        whisper: str = "none"  # in, out, both, none
    ) -> dict:
        """
        Создает snoop канал для прослушивания
        Это ключевая функция для real-time аудио!
        """
        params = {
            "spy": spy,
            "whisper": whisper,
            "app": self.app_name,
            "appArgs": f"snoop,{channel_id}"
        }
        return await self._make_request(
            "POST", 
            f"channels/{channel_id}/snoop",
            params=params
        )
    
    async def start_external_media(
        self,
        channel_id: str,
        external_host: str = "127.0.0.1:8001"
    ) -> dict:
        """
        Создает канал ExternalMedia для получения RTP потока
        """
        params = {
            "app": self.app_name,
            "external_host": external_host,
            "format": "slin16",  # 16-bit signed linear, хорошо для STT
        }
        return await self._make_request(
            "POST",
            "channels/externalMedia",
            params=params
        )
    
    async def subscribe_events(self, callback: Callable):
        """Подписывается на события ARI через WebSocket"""
        
        async def ws_handler():
            url = f"{self.ws_url}?app={self.app_name}&api_key={settings.asterisk_ari_user}:{settings.asterisk_ari_password}"
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    logger.info("Connected to ARI WebSocket")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                event = msg.json()
                                await callback(event)
                            except Exception as e:
                                logger.error(f"Event handling error: {e}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WS error: {ws.exception()}")
                            break
                            
        self._ws_task = asyncio.create_task(ws_handler())
        
    async def close(self):
        """Закрывает соединения"""
        if self._ws_task:
            self._ws_task.cancel()


class AudioStreamReceiver:
    """Приемник аудиопотока через UDP"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.transport = None
        self.audio_callbacks: dict[str, Callable] = {}
        
    async def start(self):
        """Запускает UDP сервер для приема RTP"""
        loop = asyncio.get_event_loop()
        
        class AudioProtocol(asyncio.DatagramProtocol):
            def __init__(self, receiver):
                self.receiver = receiver
                
            def datagram_received(self, data, addr):
                # RTP header is 12 bytes
                if len(data) > 12:
                    payload = data[12:]  # Skip RTP header
                    # Вызываем все зарегистрированные callbacks
                    for callback in self.receiver.audio_callbacks.values():
                        asyncio.create_task(callback(payload))
        
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: AudioProtocol(self),
            local_addr=(self.host, self.port)
        )
        logger.info(f"Audio receiver started on {self.host}:{self.port}")
        
    def register_callback(self, call_id: str, callback: Callable):
        """Регистрирует callback для обработки аудио"""
        self.audio_callbacks[call_id] = callback
        
    def unregister_callback(self, call_id: str):
        """Удаляет callback"""
        if call_id in self.audio_callbacks:
            del self.audio_callbacks[call_id]
            
    async def stop(self):
        """Останавливает сервер"""
        if self.transport:
            self.transport.close()


# Глобальные экземпляры
ari_service = AsteriskARIService()
audio_receiver = AudioStreamReceiver()
