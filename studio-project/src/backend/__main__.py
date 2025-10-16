from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict

app = FastAPI(
    title="Chat API",
    description="Knowledge Platform Chat API",
    version="0.0.1"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

@app.post("/chat")
async def send_chat_message() -> str:
    return "Message received and ignored. Over."


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)
