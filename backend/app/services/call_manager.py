"""Менеджер звонков"""
import asyncio
from datetime import datetime
from typing import Dict, Optional, Callable, List
from loguru import logger

from ..models import Call, CallStatus, CallDirection, TranscriptSegment, Suggestion, CallEvent
from .transcription import transcription_service
from .ai_agent import ai_agent


class CallManager:
    """Управляет активными звонками и их обработкой"""
    
    def __init__(self):
        self.active_calls: Dict[str, Call] = {}
        self.event_subscribers: List[Callable] = []
        self.audio_buffers: Dict[str, Dict[str, bytearray]] = {}
        self.transcription_tasks: Dict[str, asyncio.Task] = {}
        
    def subscribe(self, callback: Callable):
        """Подписывает на события звонков"""
        self.event_subscribers.append(callback)
        
    def unsubscribe(self, callback: Callable):
        """Отписывает от событий"""
        if callback in self.event_subscribers:
            self.event_subscribers.remove(callback)
            
    async def emit_event(self, event: CallEvent):
        """Отправляет событие всем подписчикам"""
        for callback in self.event_subscribers:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    async def handle_call_start(
        self, 
        call_id: str, 
        caller: str, 
        called: str,
        direction: CallDirection = CallDirection.INCOMING
    ):
        """Обрабатывает начало звонка"""
        call = Call(
            id=call_id,
            caller_number=caller,
            called_number=called,
            direction=direction,
            status=CallStatus.RINGING,
            started_at=datetime.now()
        )
        
        self.active_calls[call_id] = call
        self.audio_buffers[call_id] = {
            "operator": bytearray(),
            "client": bytearray()
        }
        
        logger.info(f"Call started: {call_id} from {caller}")
        
        await self.emit_event(CallEvent(
            event_type="call_start",
            call_id=call_id,
            data=call.model_dump(mode="json")
        ))
        
        # Запускаем фоновую задачу транскрипции
        self.transcription_tasks[call_id] = asyncio.create_task(
            self._transcription_loop(call_id)
        )
        
    async def handle_call_answer(self, call_id: str):
        """Обрабатывает ответ на звонок"""
        if call_id in self.active_calls:
            self.active_calls[call_id].status = CallStatus.ANSWERED
            self.active_calls[call_id].answered_at = datetime.now()
            
            await self.emit_event(CallEvent(
                event_type="call_answer",
                call_id=call_id,
                data={"answered_at": datetime.now().isoformat()}
            ))
            
    async def handle_call_end(self, call_id: str):
        """Обрабатывает завершение звонка"""
        if call_id in self.active_calls:
            self.active_calls[call_id].status = CallStatus.ENDED
            self.active_calls[call_id].ended_at = datetime.now()
            
            # Останавливаем транскрипцию
            if call_id in self.transcription_tasks:
                self.transcription_tasks[call_id].cancel()
                del self.transcription_tasks[call_id]
            
            await self.emit_event(CallEvent(
                event_type="call_end",
                call_id=call_id,
                data=self.active_calls[call_id].model_dump(mode="json")
            ))
            
            # Очищаем
            logger.info(f"Call ended: {call_id}")
            del self.active_calls[call_id]
            
            if call_id in self.audio_buffers:
                del self.audio_buffers[call_id]
                
            ai_agent.clear_call(call_id)
    
    def add_audio_chunk(self, call_id: str, speaker: str, audio_data: bytes):
        """Добавляет аудио-чанк в буфер"""
        if call_id in self.audio_buffers and speaker in self.audio_buffers[call_id]:
            self.audio_buffers[call_id][speaker].extend(audio_data)
            
    async def _transcription_loop(self, call_id: str):
        """Фоновая задача для периодической транскрипции"""
        CHUNK_DURATION = 3.0  # секунды
        SAMPLE_RATE = 16000
        BYTES_PER_SAMPLE = 2
        CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION * BYTES_PER_SAMPLE)
        
        while call_id in self.active_calls:
            await asyncio.sleep(CHUNK_DURATION)
            
            for speaker in ["operator", "client"]:
                if call_id not in self.audio_buffers:
                    continue
                    
                buffer = self.audio_buffers[call_id][speaker]
                
                if len(buffer) >= CHUNK_SIZE:
                    # Извлекаем чанк
                    chunk = bytes(buffer[:CHUNK_SIZE])
                    del buffer[:CHUNK_SIZE]
                    
                    # Транскрибируем
                    text = await transcription_service.transcribe_chunk(chunk)
                    
                    if text and text.strip():
                        segment = TranscriptSegment(
                            call_id=call_id,
                            timestamp=datetime.now().timestamp(),
                            speaker=speaker,
                            text=text.strip()
                        )
                        
                        # Отправляем транскрипт
                        await self.emit_event(CallEvent(
                            event_type="transcript",
                            call_id=call_id,
                            data=segment.model_dump()
                        ))
                        
                        # Анализируем через AI
                        suggestion = await ai_agent.analyze_and_suggest(
                            call_id, segment
                        )
                        
                        if suggestion:
                            await self.emit_event(CallEvent(
                                event_type="suggestion",
                                call_id=call_id,
                                data=suggestion.model_dump(mode="json")
                            ))
    
    def get_active_calls(self) -> List[Call]:
        """Возвращает список активных звонков"""
        return list(self.active_calls.values())
    
    def get_call(self, call_id: str) -> Optional[Call]:
        """Возвращает информацию о звонке"""
        return self.active_calls.get(call_id)


# Глобальный экземпляр
call_manager = CallManager()
