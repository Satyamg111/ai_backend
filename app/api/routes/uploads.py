# ============================================
# FILE:
# app/api/routes/uploads.py
# ============================================

import os
import fitz

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)
from fastapi import Depends

from app.auth.admin_auth import (
    verify_admin
)
from app.db.chroma import collection

router = APIRouter()

# ============================================
# CONFIG
# ============================================

UPLOAD_DIR = "app/data/resumes"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

# ============================================
# UPLOAD RESUME
# ============================================

@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    admin=Depends(verify_admin)
):

    # ========================================
    # VALIDATE FILE
    # ========================================

    if not file.filename.endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # ========================================
    # SAVE FILE
    # ========================================

    file_path = os.path.join(
        UPLOAD_DIR,
        "resume.pdf"
    )

    with open(file_path, "wb") as buffer:

        content = await file.read()

        buffer.write(content)

    # ========================================
    # EXTRACT PDF TEXT
    # ========================================

    try:

        doc = fitz.open(file_path)

        text = ""

        for page in doc:

            text += page.get_text()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )

    # ========================================
    # SPLIT TEXT
    # ========================================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(text)

    # ========================================
    # CLEAR OLD EMBEDDINGS
    # ========================================

    try:

        existing = collection.get()

        if existing["ids"]:

            collection.delete(
                ids=existing["ids"]
            )

    except:
        pass

    # ========================================
    # STORE NEW EMBEDDINGS
    # ========================================

    for index, chunk in enumerate(chunks):

        collection.add(
            documents=[chunk],
            ids=[str(index)]
        )

    # ========================================
    # RESPONSE
    # ========================================

    return {
        "success": True,
        "message": "Resume uploaded successfully",
        "chunks": len(chunks)
    }