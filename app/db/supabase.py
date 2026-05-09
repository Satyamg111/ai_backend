import os

# from dotenv import load_dotenv

from supabase import create_client

# load_dotenv()

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)
print("SUPABASE_URL =", SUPABASE_URL)
print("SUPABASE_KEY_PREFIX =", SUPABASE_KEY[:15] if SUPABASE_KEY else None) 
if not SUPABASE_URL or not SUPABASE_KEY:

    raise ValueError(
        "Supabase environment variables missing"
    )

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
