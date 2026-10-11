import secrets
import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    env: str = "development"
    database_url: str = "sqlite:///./bankism.db"
    intent_hmac_key: str = ""
    session_signing_key: str = ""
    allowed_origins: str = "http://localhost:5173,http://localhost:4173"
    allowed_origin_regex: str | None = None
    llm_provider: str = "gemini"
    llm_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    llm_timeout: float = 2.5
    llm_daily_budget: int = 1000
    llm_failure_threshold: int = 3
    llm_cooldown: float = 30.0
    rate_limit_per_minute: int = 120
    rate_limit_evaluate: int = 3
    intent_ttl: int = 300
    per_transaction_limit: int = 5000000
    daily_limit: int = 10000000
    serve_frontend: bool = False

    @model_validator(mode="after")
    def validate_keys(self) -> "Settings":
        if self.env == "production":
            if min(len(self.intent_hmac_key), len(self.session_signing_key)) < 32:
                raise ValueError(
                    "Production requires independent signing keys of at least 32 characters"
                )
            if self.intent_hmac_key == self.session_signing_key:
                raise ValueError("Signing keys must be independent")
            if not self.allowed_origins or "*" in self.allowed_origins:
                raise ValueError("Production requires explicit ALLOWED_ORIGINS")
        else:
            if not self.intent_hmac_key or not self.session_signing_key:
                warnings.warn(
                    "Ephemeral development keys; sessions reset on restart",
                    stacklevel=2,
                )
            self.intent_hmac_key = self.intent_hmac_key or secrets.token_hex(32)
            self.session_signing_key = self.session_signing_key or secrets.token_hex(32)
        if self.llm_provider not in {"gemini", "openai", "mock"}:
            raise ValueError("Unsupported LLM_PROVIDER")
        return self
