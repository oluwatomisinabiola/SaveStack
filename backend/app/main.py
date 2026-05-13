from fastapi import FastAPI

from app.db import engine
from app.models import Base
from app.routes.auth import router as auth_router

app = FastAPI(title="SaveStack API")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}