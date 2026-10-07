from fastapi import FastAPI

from app.controllers.chat.chat_controller import router as chat_router
from app.controllers.project.project_controller import router as project_router

from fastapi import FastAPI

from app.core.db.database import create_tables
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sivaxi AI API",
    version="1.0.0",
    swagger_ui_init_oauth={
        "clientId": "sivaxi-ai",
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://vixi.sivaxi.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()
app.include_router(chat_router)
app.include_router(project_router)

@app.get("/ping")
def root():
    return {
        "message": "Data Intellijence API is running",
        "status": "OK"
    }