from decouple import config

SERP_API_KEY = config("SERP_API_KEY")

# MongoDB
DATABASE_CONNECTION_URL = config("DATABASE_CONNECTION_URL")
DB_NAME = "grover-betaapps"

# OpenAI
OPENAI_API_KEY = config("OPENAI_API_KEY")
OPENAI_SERVICE = config("OPENAI_SERVICE", "")
OPENAI_MODEL = config("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = config('EMBEDDING_MODEL', 'text-embedding-3-small')

DEBUG = config('DEBUG', default=False, cast=bool)

# print(f"MONGODB_URI: {DATABASE_CONNECTION_URL}")
# print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")