from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import dotenv_values
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from routes import routers


config = dotenv_values('.env')

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = AsyncIOMotorClient(config['MONGODB_URI'])
    app.state.db = app.state.client[config['DB_NAME']]
    app.state.config = config
    yield
    app.state.client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with ["http://localhost:3000"] for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)

@app.get('/')
async def home():
    return {'code': 200}

if __name__ == '__main__':
    uvicorn.run(app='main:app', reload=False)