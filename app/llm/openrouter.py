import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL"
)
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL"
)

llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv(
        "OPENROUTER_API_KEY"
    ),
    streaming=True,
    temperature=0.7
)