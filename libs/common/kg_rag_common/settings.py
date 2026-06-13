from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresDsn(AnyUrl):
    allowed_schemes = {"postgres", "postgresql", "postgresql+psycopg"}
    host_required = True


class RedisDsn(AnyUrl):
    allowed_schemes = {"redis", "rediss"}
    host_required = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=('.env',), env_prefix="KG_", case_sensitive=False)

    # App
    app_name: str = Field(default="kg-rag")
    environment: Literal["dev", "staging", "prod"] = Field(default="dev")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # Services
    postgres_dsn: Optional[PostgresDsn] = Field(default=None)
    redis_dsn: RedisDsn = Field(default="redis://redis:6379/0")
    qdrant_url: str = Field(default="http://qdrant:6333")
    neo4j_url: str = Field(default="bolt://neo4j:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")

    # Object storage (MinIO)
    s3_endpoint_url: str = Field(default="http://minio:9000")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: str = Field(default="minioadmin")
    s3_bucket: str = Field(default="kg-bucket")

    # UAA (OAuth2/OIDC identity provider)
    uaa_issuer_url: str = Field(default="http://localhost:8080/uaa")
    uaa_jwks_url: Optional[str] = Field(default=None)
    uaa_client_id: str = Field(default="kg-rag-frontend")

    @property
    def uaa_jwks_uri(self) -> str:
        return self.uaa_jwks_url or f"{self.uaa_issuer_url}/token_keys"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
