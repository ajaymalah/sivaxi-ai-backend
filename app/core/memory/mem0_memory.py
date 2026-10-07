import os

from dotenv import load_dotenv
from mem0 import Memory

load_dotenv()


class Mem0Memory:

    def __init__(self):

        google_api_key = os.getenv("GOOGLE_API_KEY")
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        qdrant_collection = os.getenv(
            "QDRANT_COLLECTION",
            "mem0"
        )

        missing = []

        if not google_api_key:
            missing.append("GOOGLE_API_KEY")

        if not qdrant_url:
            missing.append("QDRANT_URL")

        if not qdrant_api_key:
            missing.append("QDRANT_API_KEY")

        if missing:
            raise RuntimeError(
                "Missing required environment variables: "
                + ", ".join(missing)
            )

        config = {
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-3.5-flash-lite",
                    "temperature": 0.2,
                    "api_key": google_api_key,
                },
            },

            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": "models/gemini-embedding-001",
                    "embedding_dims": 768,
                    "api_key": google_api_key,
                },
            },

            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": qdrant_url,
                    "api_key": qdrant_api_key,
                    "collection_name": qdrant_collection,
                    "embedding_model_dims": 768,
                },
            },
        }

        self.memory = Memory.from_config(config)

    def save(
        self,
        content: str,
        user_id: str,
        project_id: str | None = None,
    ):
        return self.memory.add(
            content,
            user_id=user_id,
        )

    def search(
        self,
        query: str,
        user_id: str,
        project_id: str | None = None,
    ):
        return self.memory.search(
            query,
            filters={"user_id": user_id},
        )