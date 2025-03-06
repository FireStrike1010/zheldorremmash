from fastapi import FastAPI
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
    yield
    app.state.client.close()


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app='main:app', reload=False)