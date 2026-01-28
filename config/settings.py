"""Configuration centralisée du projet RAG."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application RAG."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Anthropic API (Claude) ===
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # === Voyage AI API (Embeddings) ===
    voyage_api_key: str = ""
    voyage_embed_model: str = "voyage-3"

    # === Chemins ===
    data_dir: Path = Path("./data")
    pdf_dir: Path = Path("./data/pdfs")
    chroma_dir: Path = Path("./data/chroma_db")
    sqlite_path: Path = Path("./data/metadata.db")

    # === Chunking ===
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # === Retrieval ===
    default_top_k: int = 5
    min_similarity_score: float = 0.7

    # === API ===
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # === ChromaDB ===
    chroma_collection_name: str = "research_documents"

    def ensure_directories(self) -> None:
        """Crée les répertoires nécessaires s'ils n'existent pas."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
