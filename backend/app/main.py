from fastapi import FastAPI

app = FastAPI(title="SaveStack API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}