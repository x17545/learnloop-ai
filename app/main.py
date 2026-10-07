from fastapi import FastAPI

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router



app = FastAPI(
    title=settings.app_name,
    description="AI Personal Study Coach",
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "service": "LearnLoop",
        "message": "LearnLoop API is running.",
    }