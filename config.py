import os

# ==========================================
# CONFIGURATION
# ==========================================

# Clan Tag to track
CLAN_TAG: str = "#9PJRJRPC"

# Clash Royale API Base URL
API_BASE_URL: str = "https://api.clashroyale.com/v1"

# API Key Strategy:
# 1. Environment Variable (Recommended for CI/CD)
# 2. Hardcoded Fallback (For local execution without env setup)
_FALLBACK_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjkwNTVlZTVmLWExMTQtNGViNy1iNTAzLTFiNjg0YzhjN2ZhNiIsImlhdCI6MTc2NTM5MTI4Mywic3ViIjoiZGV2ZWxvcGVyLzVkZTAwM2M4LTNiMWQtZjU0NS1lYjUwLWQ1NTQxM2FiMGNkOCIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxOTEuMjE5LjE5MC42MSJdLCJ0eXBlIjoiY2xpZW50In1dfQ.2Rj7atct7KVLldoSE1r-Pw_CKFMY-dL_ATUK24D-sEn2T7mWMFGQ1IMO0UFKpJXBlftiODdmsIMEeoDR1a6cdw"

API_KEY: str = os.environ.get("CR_API_KEY") or os.environ.get("CLASH_ROYALE_API_KEY") or _FALLBACK_KEY

# Application directories
DATA_DIR: str = "data"
TEMPLATES_DIR: str = "templates"
STATIC_DIR: str = "static"

# Time-To-Live for cached data (in minutes)
CACHE_TTL_MINUTES: int = 10
