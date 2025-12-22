"""LLM settings configuration.

Centralized settings for all LLM-related API keys and configuration.
"""

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.autodiscover import ModuleType, generate_module_env, get_module_env_path
from app.lib.llm.config import LLMProviderType

_env_file_path = get_module_env_path(ModuleType.LIB, __file__)

# Load env file into os.environ for LangChain compatibility
load_dotenv(_env_file_path, override=True)


class LLMSettings(BaseSettings):
    """LLM settings loaded from envs/lib/llm.env."""

    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google API key for Gemini")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")

    LLM_PROVIDER: str = Field(
        default=LLMProviderType.LANGCHAIN.value,
        description="LLM provider (langchain, openai)",
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_env_file_path,
        extra="allow",
    )


generate_module_env(ModuleType.LIB, __file__, LLMSettings)
llm_settings = LLMSettings()
