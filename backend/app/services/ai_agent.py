"""AI Agent для генерации подсказок через OpenRouter"""
import json
from typing import Optional, List
import httpx
from loguru import logger
from ..config import get_settings
from ..models import Suggestion, TranscriptSegment
from datetime import datetime

settings = get_settings()


SYSTEM_PROMPT = """Ты — AI-ассистент для операторов колл-центра. Твоя задача анализировать разговор в реальном времени и давать оператору полезные подсказки.

ПРАВИЛА:
1. Подсказки должны быть КОРОТКИМИ и КОНКРЕТНЫМИ (1-2 предложения)
2. Реагируй на возражения клиента мгновенно
3. Предлагай upsell только если это уместно
4. Предупреждай о проблемных ситуациях

ТИПЫ ПОДСКАЗОК:
- objection: Отработка возражения клиента
- upsell: Возможность допродажи
- info: Полезная информация
- warning: Предупреждение (негатив клиента, риск потери)
- script: Рекомендуемая фраза по скрипту

ФОРМАТ ОТВЕТА (JSON):
{
    "type": "objection|upsell|info|warning|script",
    "title": "Краткий заголовок",
    "content": "Текст подсказки для оператора",
    "priority": "low|medium|high"
}

Если подсказка не нужна — верни null.

КОНТЕКСТ КОМПАНИИ:
- Компания продает услуги связи
- Основные возражения: "дорого", "подумаю", "уже есть оператор"
- Можно предлагать: скидку 10% новым клиентам, бесплатный тестовый период

ПРИМЕРЫ:

Клиент: "Это слишком дорого для нас"
Ответ: {"type": "objection", "title": "Возражение: дорого", "content": "Предложите рассрочку или скидку 10% для новых клиентов. Сравните стоимость с конкурентами.", "priority": "high"}

Клиент: "Мне нужно подумать"
Ответ: {"type": "objection", "title": "Возражение: подумаю", "content": "Уточните, что именно смущает. Предложите тестовый период 14 дней без обязательств.", "priority": "medium"}

Клиент: "Спасибо, все устраивает"
Ответ: {"type": "upsell", "title": "Возможность upsell", "content": "Клиент доволен — предложите дополнительные услуги или расширенный пакет.", "priority": "low"}
"""


class AIAgentService:
    """AI агент для анализа разговоров через OpenRouter"""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.llm_model
        self.conversation_history: dict[str, List[TranscriptSegment]] = {}
        
    def add_transcript(self, segment: TranscriptSegment):
        """Добавляет сегмент транскрипции в историю"""
        if segment.call_id not in self.conversation_history:
            self.conversation_history[segment.call_id] = []
        self.conversation_history[segment.call_id].append(segment)
        
    def get_conversation_context(self, call_id: str, last_n: int = 10) -> str:
        """Возвращает контекст разговора"""
        segments = self.conversation_history.get(call_id, [])[-last_n:]
        
        context_lines = []
        for seg in segments:
            speaker = "ОПЕРАТОР" if seg.speaker == "operator" else "КЛИЕНТ"
            context_lines.append(f"{speaker}: {seg.text}")
        
        return "\n".join(context_lines)
    
    async def analyze_and_suggest(
        self, 
        call_id: str,
        new_segment: TranscriptSegment
    ) -> Optional[Suggestion]:
        """Анализирует новый сегмент и генерирует подсказку через OpenRouter"""
        
        # Добавляем в историю
        self.add_transcript(new_segment)
        
        # Получаем контекст
        context = self.get_conversation_context(call_id)
        
        if not context:
            return None
            
        try:
            # Формируем запрос к OpenRouter
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://ai-call-agent.local",  # Required by OpenRouter
                        "X-Title": "AI Call Agent",  # Required by OpenRouter
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {
                                "role": "user", 
                                "content": f"Текущий разговор:\n\n{context}\n\nПоследняя реплика от {'оператора' if new_segment.speaker == 'operator' else 'клиента'}: \"{new_segment.text}\"\n\nНужна ли подсказка оператору?"
                            }
                        ],
                        "temperature": settings.llm_temperature,
                        "max_tokens": 300,
                        "response_format": {"type": "json_object"}
                    }
                )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None
            
            result_data = response.json()
            result = result_data["choices"][0]["message"]["content"]
            
            if result and result.strip() != "null":
                data = json.loads(result)
                if data:
                    return Suggestion(
                        call_id=call_id,
                        type=data.get("type", "info"),
                        title=data.get("title", "Подсказка"),
                        content=data.get("content", ""),
                        priority=data.get("priority", "medium"),
                        created_at=datetime.now()
                    )
                    
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
        except httpx.TimeoutException:
            logger.error("OpenRouter request timeout")
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            
        return None
    
    def clear_call(self, call_id: str):
        """Очищает историю звонка"""
        if call_id in self.conversation_history:
            del self.conversation_history[call_id]


# Глобальный экземпляр
ai_agent = AIAgentService()
