from fastapi import FastAPI
from .auth import router as auth_router
from .userdb import init_db

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router)