from fastapi import FastAPI

app = FastAPI(
    title="LearnLoop API",
    description="AI Personal Study Coach",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "service": "LearnLoop",
        "message": "LearnLoop API is running.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }