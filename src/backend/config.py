import os
import secrets
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:10090")
DISCOVERY_URL = os.getenv(
    "OAUTH_DISCOVERY_URL",
    "http://auth.localhost:9000/application/o/kg/.well-known/openid-configuration"
)
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "rkuclih8uzm44nTUvwasexioUKFk5aG1zhG8jcJX")
CLIENT_SECRET = os.getenv(
    "OAUTH_CLIENT_SECRET",
    "NEb0sAcMc2kTTdvfJMctLYE35Fp0GqyqFp4oOVrstxsevnVMJutiIhvb6TzwPrkbphAh1EiI74oRRO79xRCoZTh1suFYTV9J0tmRJBIFIF4znDYwNyDp3IzUQlESvaS0"
)
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))

LLM_WORKER_URL = os.getenv("LLM_WORKER_URL", "http://localhost")
LLM_WORKER_PORT = os.getenv("LLM_WORKER_PORT", "9200")