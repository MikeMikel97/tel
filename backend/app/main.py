"""FastAPI Application - AI Call Agent"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from .config import get_settings
from .models import Call, CallEvent, Suggestion
from .services.call_manager import call_manager
from .services.asterisk_ari import ari_service, audio_receiver
from .api import auth, admin

settings = get_settings()


# Менеджер WebSocket соединений
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
        
    async def broadcast(self, event: CallEvent):
        """Отправляет событие всем подключенным клиентам"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(event.model_dump(mode="json"))
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.append(connection)
                
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения"""
    logger.info("Starting AI Call Agent...")
    
    # Подписываем WebSocket manager на события звонков
    call_manager.subscribe(ws_manager.broadcast)
    
    # Запускаем audio receiver (для real-time)
    # await audio_receiver.start()
    
    # Подключаемся к Asterisk ARI
    # async def handle_ari_event(event):
    #     logger.debug(f"ARI Event: {event}")
    # await ari_service.subscribe_events(handle_ari_event)
    
    logger.info("AI Call Agent started!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    call_manager.unsubscribe(ws_manager.broadcast)
    # await audio_receiver.stop()
    # await ari_service.close()


app = FastAPI(
    title="AI Call Agent",
    description="Real-time AI assistant for call center operators",
    version="1.0.0",
    lifespan=lifespan
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


# === REST API Endpoints ===

@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Call Agent API", "time": datetime.now().isoformat()}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "asterisk": settings.asterisk_host,
        "active_calls": len(call_manager.active_calls),
        "ws_connections": len(ws_manager.active_connections)
    }


@app.get("/api/calls", response_model=List[Call])
async def get_active_calls():
    """Получить список активных звонков"""
    return call_manager.get_active_calls()


@app.get("/api/calls/{call_id}")
async def get_call(call_id: str):
    """Получить информацию о звонке"""
    call = call_manager.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


# === AGI Endpoints (для Asterisk) ===

@app.get("/agi/call_start")
async def agi_call_start(caller: str, id: str, called: str = ""):
    """AGI callback при начале звонка"""
    await call_manager.handle_call_start(
        call_id=id,
        caller=caller,
        called=called or settings.asterisk_host
    )
    return {"status": "ok"}


@app.get("/agi/call_end")
async def agi_call_end(id: str):
    """AGI callback при завершении звонка"""
    await call_manager.handle_call_end(call_id=id)
    return {"status": "ok"}


# === WebSocket для real-time ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для получения событий в реальном времени"""
    await ws_manager.connect(websocket)
    
    # Отправляем текущее состояние
    for call in call_manager.get_active_calls():
        await websocket.send_json({
            "event_type": "call_start",
            "call_id": call.id,
            "data": call.model_dump(mode="json")
        })
    
    try:
        while True:
            # Просто держим соединение открытым
            # События приходят через broadcast
            data = await websocket.receive_text()
            
            # Можно обрабатывать команды от клиента
            if data == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# === Demo endpoint для тестирования ===

@app.post("/api/demo/call")
async def demo_start_call():
    """Создает тестовый звонок для демонстрации"""
    import uuid
    call_id = str(uuid.uuid4())[:8]
    
    await call_manager.handle_call_start(
        call_id=call_id,
        caller="+79001234567",
        called="+79918987423"
    )
    
    # Эмулируем ответ через 2 секунды
    asyncio.create_task(_demo_call_flow(call_id))
    
    return {"call_id": call_id, "status": "started"}


async def _demo_call_flow(call_id: str):
    """Эмулирует поток звонка для демо"""
    from .models import TranscriptSegment, CallDirection
    from .services.ai_agent import ai_agent
    
    await asyncio.sleep(2)
    await call_manager.handle_call_answer(call_id)
    
    # Симулируем диалог
    demo_dialog = [
        ("client", "Здравствуйте, я хотел бы узнать про ваши тарифы на связь"),
        ("operator", "Добрый день! Конечно, расскажу вам о наших тарифах. Какой объем звонков вас интересует?"),
        ("client", "Ну примерно 1000 минут в месяц. Но честно говоря, это слишком дорого для нас"),
        ("operator", "Понимаю вашу озабоченность. Давайте посмотрим, что можем предложить"),
        ("client", "Мне нужно подумать, я перезвоню"),
    ]
    
    for speaker, text in demo_dialog:
        await asyncio.sleep(3)
        
        if call_id not in call_manager.active_calls:
            break
            
        segment = TranscriptSegment(
            call_id=call_id,
            timestamp=datetime.now().timestamp(),
            speaker=speaker,
            text=text
        )
        
        # Отправляем транскрипт
        await call_manager.emit_event(CallEvent(
            event_type="transcript",
            call_id=call_id,
            data=segment.model_dump()
        ))
        
        # Анализируем AI
        suggestion = await ai_agent.analyze_and_suggest(call_id, segment)
        
        if suggestion:
            await call_manager.emit_event(CallEvent(
                event_type="suggestion",
                call_id=call_id,
                data=suggestion.model_dump(mode="json")
            ))
    
    # Завершаем звонок через 5 секунд после последней реплики
    await asyncio.sleep(5)
    if call_id in call_manager.active_calls:
        await call_manager.handle_call_end(call_id)


@app.post("/api/demo/end/{call_id}")
async def demo_end_call(call_id: str):
    """Завершает демо-звонок"""
    await call_manager.handle_call_end(call_id)
    return {"status": "ended"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
