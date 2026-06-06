from fastapi import FastAPI
from app.api.router import api_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Multi-Agent Backend",
    version="1.0.0"
)

# ============================================
# OPENAPI SWAGGER UI FIX FOR FILE UPLOADS
# ============================================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Multi-Agent Backend",
        version="1.0.0",
        routes=app.routes,
    )
    
    # Swagger UI requires format: binary to display file upload inputs
    # instead of contentMediaType: application/octet-stream.
    def fix_openapi_multipart_files(d):
        if isinstance(d, dict):
            if d.get("contentMediaType") == "application/octet-stream":
                d["format"] = "binary"
                del d["contentMediaType"]
            for k, v in d.items():
                fix_openapi_multipart_files(v)
        elif isinstance(d, list):
            for item in d:
                fix_openapi_multipart_files(item)

    fix_openapi_multipart_files(openapi_schema)
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)