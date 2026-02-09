import os
import boto3
from google.genai import Client
from google.genai.types import HttpRetryOptions
from google.adk.models.google_llm import Gemini

GEMINI_25_PRO = "gemini-2.5-pro"
GEMINI_3_FLASH = "gemini-3-flash-preview"
GEMINI_3_PRO = "gemini-3-pro-preview"
GEMINI_25_FLASH = "gemini-2.5-flash"
GEMINI_25_FLASH_LITE = "gemini-2.5-flash-lite"

RETRY_CONFIG = HttpRetryOptions(
    attempts=3,
    initial_delay=1,
    exp_base=2,
    http_status_codes=[429, 500, 503]
)

ACTIVE_FLASH_MODEL = Gemini(model=GEMINI_3_FLASH, retry_options=RETRY_CONFIG)
ACTIVE_PRO_MODEL = Gemini(model=GEMINI_3_PRO, retry_options=RETRY_CONFIG)

# Initialize Google GenAI client
# Fallback to project ID and location if GOOGLE_API_KEY is not set
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    google_genai_client = Client(api_key=api_key)
else:
    google_genai_client = Client(
        vertexai=True,
        project="project-1023a394-e63c-4912-8ed",
        location="global"
    )

# Initialize S3 client for Publisher Agent
# Note: CLOUDFLARE_ACCOUNT_ID is used to construct the endpoint URL.
# If not present, endpoint_url will be invalid until used.
s3_endpoint_url = f"https://{os.environ.get('CLOUDFLARE_ACCOUNT_ID')}.r2.cloudflarestorage.com"
s3_client = boto3.client(
    's3',
    endpoint_url=s3_endpoint_url
)

PLUTUS_BASE_URL = os.environ.get("PLUTUS_API_BASE_URL", "https://plutus-server-268314723675.us-central1.run.app/")
PLUTUS_API_KEY = os.environ.get("PLUTUS_API_KEY", "test")
