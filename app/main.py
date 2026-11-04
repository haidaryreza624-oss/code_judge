from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.submissions import router as submission_router
from app.api.languages import router as language_router

from app.services.queue_manager import queue_manager


@asynccontextmanager
async def lifespan(app: FastAPI):

    await queue_manager.start()

    yield

    await queue_manager.stop()


app = FastAPI(
    title="CodeArena Judge Engine",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(submission_router)
app.include_router(language_router)