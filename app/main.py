from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import contributors


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="GitHub Metrics Service", version="0.1.0", lifespan=lifespan)

app.include_router(contributors.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
