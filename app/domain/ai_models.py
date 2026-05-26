from enum import StrEnum


class ProviderKind(StrEnum):
    OPENAI = "openai"
    BEDROCK_OPENAI = "bedrock_openai"
    OLLAMA = "ollama"


class ModelProfileKind(StrEnum):
    LLM = "llm"
    EMBEDDING = "embedding"

