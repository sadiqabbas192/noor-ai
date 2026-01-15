from fastapi import FastAPI
from interfaces.api import router as api_router
from core.config import DEBUG_MODE
import uvicorn

app = FastAPI(title="Noor-AI API", version="1.1.0-dev")

app.include_router(api_router)

# Basic root endpoint for convenience? Not requested, but health is there.
# The prompt only asked for specific routes.

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=DEBUG_MODE)
