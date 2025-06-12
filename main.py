from contextlib import asynccontextmanager
import logging
import uvicorn
import json
import asyncio
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from db.base import engine, Base, create_database
from typing import List



logger = logging.getLogger("uvicorn.access")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# буфер последних сообщений
_events_buffer: List[dict] = []
BUFFER_SIZE = 100  # сколько последних событий держим

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: ---
    consumer = AIOKafkaConsumer(
        "ad-events.ad-events",
        bootstrap_servers="localhost:9092",
        group_id="mobile-proxy-group",
        auto_offset_reset="latest",
    )
    await consumer.start()
#
    async def consume_loop():
        async for msg in consumer:
            try:
                evt = json.loads(msg.value.decode())
            except:
                continue
            _events_buffer.append(evt)
            if len(_events_buffer) > BUFFER_SIZE:
                _events_buffer.pop(0)

    # в фоне
    asyncio.create_task(consume_loop())
    #pass
    yield
    # --- Shutdown: ---

app = FastAPI(
    title="Ad Service API",
    version="0.1.0",
    lifespan=lifespan
)

# --- Global CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# --- Роутеры ---
from routers import auth, cities, categories, offers
app.include_router(auth.router)
app.include_router(cities.router)
app.include_router(categories.router)
app.include_router(offers.router)

@app.get("/api/kafka/events")
async def get_events():
    return {"events": list(_events_buffer)}

if __name__ == "__main__":
    #asyncio.run(create_database())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
