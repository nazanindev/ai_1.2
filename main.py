import logging

from fastapi import FastAPI

from database import Base, engine
from routers import webhooks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="GitHub Metrics Service")

Base.metadata.create_all(bind=engine)

app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
