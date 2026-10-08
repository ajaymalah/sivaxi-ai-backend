from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.chat.chat_controller import router as chat_router
from app.controllers.project.project_controller import router as project_router

from app.core.db.database import create_tables
from app.core.langgraph.langgraph import AppLangGraph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database tables
    create_tables()

    # Create ONE LangGraph instance per FastAPI process
    app.state.app_lang_graph = AppLangGraph()

    try:
        yield

    finally:
        # Close LangGraph/PostgresSaver when the process shuts down
        app.state.app_lang_graph.close()


app = FastAPI(
    title="Sivaxi AI API",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "clientId": "sivaxi-ai",
        "usePkceWithAuthorizationCodeGrant": True,
    },
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://vixi.sivaxi.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(project_router)


@app.get("/ping")
def root():
    return {
        "message": "Data Intellijence API is running",
        "status": "OK",
    }