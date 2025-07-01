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
    app.state.client = AsyncIOMotorClient(
        host=os.getenv('MONGO_HOST'),
        port=int(os.getenv('MONGO_PORT')),
        username=os.getenv('MONGO_INITDB_ROOT_USERNAME'),
        password=os.getenv('MONGO_INITDB_ROOT_PASSWORD'),
        authSource = os.getenv('AUTH_SOURCE', 'admin')
        )
    app.state.db = app.state.client[os.getenv('MONGO_DBNAME')]
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


app = FastAPI(lifespan=lifespan, root_path="/api", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)

@app.get('/')
async def home():
    return {'status_code': 200, "server_running": True}