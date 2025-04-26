import os


class Settings: # type: ignore
    def get_url(self) -> str:
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "786811")
        db = os.getenv("POSTGRES_DB", "diplom")
        server = os.getenv("POSTGRES_SERVER", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

settings = Settings()