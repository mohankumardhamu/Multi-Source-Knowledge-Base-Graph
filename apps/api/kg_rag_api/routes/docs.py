from __future__ import annotations

import hashlib
import io
import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi import Form
from typing import List
from pathlib import Path as _P
from sqlalchemy.orm import Session

from libs.common.kg_rag_common.settings import get_settings
from libs.common.kg_rag_common.models import Document, IngestionStatus
from apps.workers.kg_rag_workers.worker import make_celery
from ..db import session_scope


router = APIRouter(prefix="/v1/docs", tags=["docs"])

DOCS_BUCKET = "docs"


def get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


def ensure_bucket(client, bucket_name: str) -> None:
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError:
        try:
            client.create_bucket(Bucket=bucket_name)
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to ensure bucket: {e}")


def get_db() -> Session:
    with session_scope() as s:
        yield s


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    domain: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256 = hashlib.sha256(content).hexdigest()
    doc_id = uuid.uuid4()
    s3_key = f"documents/{doc_id}.pdf"

    s3 = get_s3_client()
    ensure_bucket(s3, DOCS_BUCKET)
    try:
        s3.upload_fileobj(
            Fileobj=io.BytesIO(content),
            Bucket=DOCS_BUCKET,
            Key=s3_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to object storage: {e}")

    doc = Document(
        id=doc_id,
        title=title,
        domain=domain,
        s3_bucket=DOCS_BUCKET,
        s3_key=s3_key,
        checksum_sha256=sha256,
        status="queued",
    )
    db.add(doc)
    db.flush()

    ingest = IngestionStatus(
        document_id=doc.id, status="queued", stages={"events": []}
    )
    db.add(ingest)

    # Enqueue Celery task
    celery = make_celery()
    celery.send_task("ingest.process", args=[str(doc.id)])

    return {"id": str(doc.id), "status": doc.status}


@router.get("/{doc_id}/status")
def get_status(doc_id: uuid.UUID, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    status_row = (
        db.query(IngestionStatus).filter(IngestionStatus.document_id == doc.id).one_or_none()
    )
    stages = status_row.stages if status_row and status_row.stages else {"events": []}
    return {"status": status_row.status if status_row else doc.status, "stages": stages}


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def upload_documents_bulk(
    files: List[UploadFile] = File(...),
    domain: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    s3 = get_s3_client()
    ensure_bucket(s3, DOCS_BUCKET)
    celery = make_celery()

    results: list[dict[str, str]] = []
    for f in files:
        try:
            if f.content_type not in ("application/pdf", "application/octet-stream"):
                results.append({
                    "filename": f.filename or "",
                    "error": "Only PDF files are accepted",
                })
                continue

            content = await f.read()
            if not content:
                results.append({
                    "filename": f.filename or "",
                    "error": "Empty file",
                })
                continue

            sha256 = hashlib.sha256(content).hexdigest()
            doc_id = uuid.uuid4()
            s3_key = f"documents/{doc_id}.pdf"

            # upload to S3
            s3.upload_fileobj(
                Fileobj=io.BytesIO(content),
                Bucket=DOCS_BUCKET,
                Key=s3_key,
                ExtraArgs={"ContentType": "application/pdf"},
            )

            title = _P(f.filename or str(doc_id)).stem
            doc = Document(
                id=doc_id,
                title=title,
                domain=domain,
                s3_bucket=DOCS_BUCKET,
                s3_key=s3_key,
                checksum_sha256=sha256,
                status="queued",
            )
            db.add(doc)
            db.flush()

            ingest = IngestionStatus(
                document_id=doc.id, status="queued", stages={"events": []}
            )
            db.add(ingest)

            # enqueue
            celery.send_task("ingest.process", args=[str(doc.id)])

            results.append({
                "filename": f.filename or title,
                "id": str(doc.id),
                "status": "queued",
            })
        except ClientError as e:
            results.append({
                "filename": f.filename or "",
                "error": f"Failed to upload: {e}",
            })
        except Exception as e:
            results.append({
                "filename": f.filename or "",
                "error": str(e),
            })

    return {"results": results}
