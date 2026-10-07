from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.models.document_page import DocumentPage
from app.services.pdf_service import extract_pdf_text
from app.models.document_chunk import DocumentChunk
from app.services.chunk_service import chunk_text
from app.schemas.search import SearchRequest, SearchResponse
from app.services.vector_service import search_chunks


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file is not allowed.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 20MB.",
        )

    original_filename = file.filename or "document.pdf"

    stored_filename = f"{uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / stored_filename

    file_path.write_bytes(content)

    document = Document(
        user_id=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        content_type=file.content_type,
        status="uploaded",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        pages = extract_pdf_text(str(file_path))

        has_text = any(
            page["text"].strip()
            for page in pages
        )

        if not has_text:
            document.status = "failed"
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No extractable text was found in the PDF.",
            )

        for page in pages:
            page_number = page["page"]
            page_text = page["text"]

            document_page = DocumentPage(
                document_id=document.id,
                page_number=page_number,
                text=page_text,
            )
            db.add(document_page)

            chunks = chunk_text(page_text)

            for chunk_index, chunk in enumerate(chunks):
                document_chunk = DocumentChunk(
                    document_id=document.id,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=chunk,
                )
                db.add(document_chunk)

        document.status = "processed"

        db.commit()
        db.refresh(document)

        return document

    except HTTPException:
        raise

    except Exception as exc:
        document.status = "failed"
        db.commit()

        print("PDF processing error:", repr(exc))


        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF.",
        )


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    ).all()

    return documents


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.post(
    "/{document_id}/search",
    response_model=SearchResponse,
)
def search_document(
    document_id: int,
    search_data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    result = search_chunks(
        query=search_data.query,
        document_id=document_id,
        limit=search_data.limit,
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    results = []

    for index, text in enumerate(documents):
        metadata = metadatas[index]

        results.append(
            {
                "text": text,
                "page_number": metadata["page_number"],
                "chunk_index": metadata["chunk_index"],
                "distance": distances[index]
                if index < len(distances)
                else None,
            }
        )

    return {
        "document_id": document_id,
        "query": search_data.query,
        "results": results,
    }