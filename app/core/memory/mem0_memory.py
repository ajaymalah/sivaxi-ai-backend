from dotenv import load_dotenv

load_dotenv()

import os

from mem0 import Memory


class Mem0Memory:

    def __init__(self):
        config = {
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-3.5-flash-lite",
                    "temperature": 0.2,
                    "api_key": os.getenv("GOOGLE_API_KEY"),
                },
            },

            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": "models/gemini-embedding-001",
                    "embedding_dims": 768,
                    "api_key": os.getenv("GOOGLE_API_KEY"),
                },
            },

            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333,
                    "collection_name": "mem0",
                    "embedding_model_dims": 768,
                },
            },
        }

        self.memory = Memory.from_config(config)

    def save(
        self,
        content: str,
        user_id: str,
        project_id: str | None = None
    ):
        return self.memory.add(
            content,
            user_id=user_id,
        )

    def search(
        self,
        query: str,
        user_id: str,
        project_id: str | None = None
    ):
        return self.memory.search(
            query,
            filters={"user_id": user_id}
        )