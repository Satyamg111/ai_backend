import os

from fastapi import (
    Header,
    HTTPException
)

ADMIN_API_KEY = os.getenv(
    "ADMIN_API_KEY"
)

def verify_admin(
    x_admin_key: str = Header(None)
):

    if not x_admin_key:

        raise HTTPException(
            status_code=401,
            detail="Admin key missing"
        )

    if x_admin_key != ADMIN_API_KEY:

        raise HTTPException(
            status_code=403,
            detail="Invalid admin key"
        )

    return True