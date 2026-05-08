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
    model=OPENAI_MODEL,
    base_url=OPENAI_BASE_URL,
    api_key=OPENROUTER_API_KEY,
    temperature=0.7,
)