"""Сервис транскрипции аудио через Soniox"""
import asyncio
import os
from typing import AsyncGenerator, Optional
from soniox.speech_service import SpeechClient
from soniox.transcribe_file import transcribe_file_short
from loguru import logger
from ..config import get_settings

settings = get_settings()


class TranscriptionService:
    """Сервис для транскрипции аудио через Soniox API"""
    
    def __init__(self):
        self.client = SpeechClient(api_key=settings.soniox_api_key)
        
    async def transcribe_file(self, audio_path: str) -> str:
        """Транскрибирует аудиофайл"""
        try:
            # Soniox требует определенный формат аудио
            # Конвертируем если нужно
            audio_path_converted = await self._prepare_audio(audio_path)
            
            # Транскрибируем через Soniox
            result = await asyncio.to_thread(
                transcribe_file_short,
                audio_path_converted,
                settings.soniox_api_key,
                model=settings.soniox_model,
                sample_rate_hertz=settings.soniox_sample_rate
            )
            
            # Извлекаем текст из результата
            if result and hasattr(result, 'words'):
                text = ' '.join([word.text for word in result.words])
                return text
            
            return ""
            
        except Exception as e:
            logger.error(f"Soniox transcription error: {e}")
            return ""
    
    async def _prepare_audio(self, audio_path: str) -> str:
        """
        Подготавливает аудио для Soniox
        Soniox требует: WAV, 16kHz, mono, 16-bit PCM
        """
        try:
            from pydub import AudioSegment
            
            # Загружаем аудио
            audio = AudioSegment.from_file(audio_path)
            
            # Конвертируем в нужный формат
            audio = audio.set_frame_rate(settings.soniox_sample_rate)
            audio = audio.set_channels(1)  # mono
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Сохраняем во временный файл
            temp_path = audio_path.replace('.wav', '_soniox.wav')
            audio.export(temp_path, format='wav')
            
            return temp_path
            
        except Exception as e:
            logger.warning(f"Audio preparation error: {e}, using original file")
            return audio_path
    
    async def transcribe_chunk(self, audio_data: bytes, format: str = "wav") -> str:
        """Транскрибирует аудио-чанк"""
        import tempfile
        
        try:
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            result = await self.transcribe_file(temp_path)
            
            # Удаляем временный файл
            os.unlink(temp_path)
            if os.path.exists(temp_path.replace('.wav', '_soniox.wav')):
                os.unlink(temp_path.replace('.wav', '_soniox.wav'))
            
            return result
        except Exception as e:
            logger.error(f"Chunk transcription error: {e}")
            return ""


class RealtimeTranscriptionService:
    """Сервис real-time транскрипции через Soniox Streaming API"""
    
    def __init__(self):
        self.api_key = settings.soniox_api_key
        self.client = SpeechClient(api_key=self.api_key)
        
    async def stream_transcribe(
        self, 
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[str, None]:
        """
        Потоковая транскрипция аудио через Soniox
        """
        from soniox.speech_service import RecognizeRequest, RecognitionConfig
        
        try:
            # Настройки распознавания
            config = RecognitionConfig(
                model=settings.soniox_model,
                sample_rate_hertz=settings.soniox_sample_rate,
                enable_interim_results=True,
                enable_punctuation=True,
            )
            
            # Создаем streaming запрос
            async def audio_generator():
                """Генератор аудио чанков"""
                async for chunk in audio_stream:
                    yield RecognizeRequest(audio_content=chunk)
            
            # Запускаем распознавание
            responses = self.client.transcribe_stream(
                audio_generator(),
                config
            )
            
            # Возвращаем результаты
            for response in responses:
                if response.results:
                    for result in response.results:
                        if result.alternatives:
                            transcript = result.alternatives[0].transcript
                            if transcript.strip():
                                yield transcript
                                
        except Exception as e:
            logger.error(f"Soniox streaming error: {e}")


# Глобальный экземпляр
transcription_service = TranscriptionService()
realtime_transcription = RealtimeTranscriptionService()
