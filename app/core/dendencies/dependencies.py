from fastapi import Request

from app.core.langgraph.langgraph import AppLangGraph


def get_app_lang_graph(request: Request) -> AppLangGraph:
    return request.app.state.app_lang_graph