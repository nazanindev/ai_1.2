from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from database import Base, engine
from routes.pulls import router as pulls_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="GitHub Metrics Service", lifespan=lifespan)
app.include_router(pulls_router)
