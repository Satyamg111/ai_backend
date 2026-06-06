import os
import fitz
import shutil
from typing import List, Optional

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
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    admin=Depends(verify_admin)
):

    # ========================================
    # CONSOLIDATE AND VALIDATE ALL FILES
    # ========================================

    uploaded_files = []
    if file is not None and file.filename:
        uploaded_files.append(file)
    if files is not None:
        for f in files:
            if f.filename:
                uploaded_files.append(f)

    if not uploaded_files:
        raise HTTPException(
            status_code=400,
            detail="No PDF files uploaded. Provide file(s) under 'file' or 'files' form parameters."
        )

    for f in uploaded_files:
        if not f.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are allowed. Invalid file: {f.filename}"
            )

    # ========================================
    # CLEAR OLD FILES & EMBEDDINGS
    # ========================================

    try:
        if os.path.exists(UPLOAD_DIR):
            for item in os.listdir(UPLOAD_DIR):
                item_path = os.path.join(UPLOAD_DIR, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
    except Exception as e:
        print(f"Error clearing upload directory: {e}")

    try:
        existing = collection.get()
        if existing["ids"]:
            collection.delete(
                ids=existing["ids"]
            )
    except:
        pass

    # ========================================
    # PROCESS FILES
    # ========================================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    all_chunks = []

    for f in uploaded_files:
        filename = os.path.basename(f.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            content = await f.read()
            buffer.write(content)

        # Extract text
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF processing failed for {filename}: {str(e)}"
            )

        # Split text into chunks
        chunks = splitter.split_text(text)
        all_chunks.extend(chunks)

    # ========================================
    # STORE NEW EMBEDDINGS (BATCHED)
    # ========================================

    if all_chunks:
        ids = [str(index) for index in range(len(all_chunks))]
        collection.add(
            documents=all_chunks,
            ids=ids
        )

    # ========================================
    # RESPONSE
    # ========================================

    return {
        "success": True,
        "message": f"{len(uploaded_files)} resume(s) uploaded and processed successfully",
        "chunks": len(all_chunks)
    }