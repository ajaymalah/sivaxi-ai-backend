import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

from app.core.constants.constants import DEFAULT_SYSTEM_PROMPT

load_dotenv()


class GeminiLLM:

    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    def bind_tools(self, tools):

        self.llm = self.llm.bind_tools(tools)

        return self

    def invoke(
        self,
        messages,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ):

        messages = [
            SystemMessage(content=system_prompt),
            *messages
        ]

        return self.llm.invoke(messages)