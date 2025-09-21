# main.py
import asyncio
import logging
import os
from typing import List, Dict

import telegram
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Конфигурация ---
# ЗАМЕНИТЕ ЭТИ ЗНАЧЕНИЯ НА ВАШИ
# Для безопасности, рекомендуется хранить их в переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Модели данных ---
class RealEstateItem(BaseModel):
    id: int
    title: str
    description: str
    price: float
    image_url: str

# --- "База данных" в памяти (для простоты) ---
db: Dict[int, RealEstateItem] = {}
next_id = 1

# --- Приложение FastAPI ---
app = FastAPI(title="Real Estate API")

# --- Настройка CORS ---
# Позволяет вашему фронтенду на Vercel общаться с бэкендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Управление WebSocket соединениями ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- Функции для работы с Telegram ---
async def send_telegram_log(message: str):
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        logger.warning("Telegram-токен или Chat ID не установлены. Лог не будет отправлен.")
        return
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")

# --- API эндпоинты ---
@app.get("/listings", response_model=List[RealEstateItem])
async def get_listings():
    """Возвращает список всех объектов недвижимости."""
    return list(db.values())

@app.post("/listings", response_model=RealEstateItem)
async def create_listing(item: RealEstateItem):
    """Создает новый объект недвижимости и оповещает всех."""
    global next_id
    item.id = next_id
    db[next_id] = item
    next_id += 1
    
    await manager.broadcast(item.json())
    
    log_message = f"Новый объект: {item.title}\nЦена: {item.price}"
    await send_telegram_log(log_message)
    
    return item

# --- WebSocket эндпоинт для real-time обновлений ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Главная функция для запуска ---
if __name__ == "__main__":
    # Добавим несколько объектов для примера при старте
    db[0] = RealEstateItem(id=0, title="Роскошная вилла у моря", description="Панорамный вид на океан, собственный бассейн.", price=550000, image_url="https://via.placeholder.com/400x250.png/007BFF/FFFFFF?text=Villa")
    next_id = 1
    
    logger.info("Запуск сервера...")
    uvicorn.run(app, host="0.0.0.0", port=8000)