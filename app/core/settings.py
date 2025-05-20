import os
from pathlib import Path

class Settings: # type: ignore
    root_path = Path(__file__).parent.parent.parent
    uploads_path = root_path / 'uploads'
    db_path = root_path / 'vector_db'
    def get_url(self) -> str:
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "786811")
        db = os.getenv("POSTGRES_DB", "diplom")
        server = os.getenv("POSTGRES_SERVER", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

settings = Settings()