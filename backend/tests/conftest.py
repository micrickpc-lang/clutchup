import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("BOT_TOKEN", "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
os.environ.setdefault("FACEIT_API_KEY", "test")
os.environ.setdefault("FACEIT_REDIRECT_URI", "https://example.test/api/faceit/oauth/callback")
os.environ.setdefault("FRONTEND_URL", "https://example.test")
os.environ.setdefault("TELEGRAM_BOT_USERNAME", "test_bot")
os.environ.setdefault("ENVIRONMENT", "test")
