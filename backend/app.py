from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from routes import routers
from database import model_list, Audit


load_dotenv('.env')

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    app.state.db = app.state.client[os.getenv('DB_NAME')]
    await init_beanie(app.state.db, document_models=model_list)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        Audit._update_audits_status,
        "interval",
        minutes=1
    )
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    app.state.client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "DELETE", "PUT", "PATCH"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)

@app.get('/')
async def home():
    return {'status_code': 200}