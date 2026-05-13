from fastapi import FastAPI

from app.routes.auth import router as auth_router

app = FastAPI(title="SaveStack API")

app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}