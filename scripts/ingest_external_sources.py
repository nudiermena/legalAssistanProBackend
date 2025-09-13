import os
import sys
import logging
import argparse
import httpx
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import POSTGRES_URL, MISTRAL_API_KEY
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.mistral import MistralEmbedder
from agno.document import Document
from utils.pdf_processor import extract_text_from_pdf_content, sanitize_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def to_psycopg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def fetch_google_drive_pdf(file_id_or_url: str) -> bytes:
    # Accept a full drive URL or a bare file id
    if "drive.google.com" in file_id_or_url:
        # Extract id between /d/ and /view
        try:
            file_id = file_id_or_url.split("/d/")[1].split("/")[0]
        except Exception:
            raise ValueError("Could not parse Google Drive file id from URL")
    else:
        file_id = file_id_or_url
    export_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    logger.info("Downloading PDF from Google Drive...")
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        resp = client.get(export_url)
        resp.raise_for_status()
        return resp.content


def fetch_google_sheet_csv(sheet_url: str) -> str:
    # Expect a docs.google.com/spreadsheets URL and convert to CSV export
    if "docs.google.com/spreadsheets" not in sheet_url:
        raise ValueError("Expected a Google Sheets URL")
    base = sheet_url.split("/edit")[0]
    # Attempt to preserve gid if present
    gid = None
    if "gid=" in sheet_url:
        try:
            gid = sheet_url.split("gid=")[1].split("#")[0]
        except Exception:
            gid = None
    csv_url = base + "/export?format=csv"
    if gid:
        csv_url += f"&gid={gid}"
    logger.info("Downloading CSV from Google Sheets...")
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        resp = client.get(csv_url)
        resp.raise_for_status()
        return resp.text


def csv_to_text_table(csv_text: str, max_rows: int = 500) -> str:
    # Lightweight CSV to plain text table for embedding
    lines = csv_text.splitlines()
    if not lines:
        return ""
    # Truncate rows for safety
    header = lines[0]
    rows = lines[1:max_rows+1]
    return "\n".join([header] + rows)


def build_documents(pdf_bytes: bytes, sheet_text: str) -> List[Document]:
    documents: List[Document] = []

    # PDF -> text
    pdf_text_raw = extract_text_from_pdf_content(pdf_bytes)
    pdf_text = sanitize_text(pdf_text_raw or "")
    if pdf_text:
        documents.append(
            Document(
                id=None,
                name="Compendio de Jurisprudencia (PDF)",
                content=pdf_text,
                meta_data={"source": "google_drive_pdf"}
            )
        )
    else:
        logger.warning("No text extracted from PDF")

    # Sheet -> text table
    sheet_text_clean = sanitize_text(sheet_text)
    if sheet_text_clean:
        documents.append(
            Document(
                id=None,
                name="Sentencias por incluir (Google Sheets)",
                content=sheet_text_clean,
                meta_data={"source": "google_sheet"}
            )
        )
    else:
        logger.warning("No text extracted from Google Sheet")

    return documents


def upsert_documents(documents: List[Document]):
    if not documents:
        logger.info("No documents to upsert")
        return

    db_url = to_psycopg_url(POSTGRES_URL)

    embedder = MistralEmbedder(
        id="mistral-embed",
        dimensions=1024,
        api_key=MISTRAL_API_KEY,
    )

    # 1. Insert into document_templates (for template-based AI agents)
    vector_db_templates = PgVector(
        table_name="document_templates",
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=embedder,
    )

    logger.info(f"Upserting {len(documents)} documents into document_templates...")
    vector_db_templates.upsert(documents)
    logger.info("document_templates upsert complete.")

    # 2. Also insert into legal_documents_ai (for general legal AI agents)
    vector_db_legal = PgVector(
        table_name="legal_documents_ai",
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=embedder,
    )

    # Transform documents to match legal_documents_ai schema
    legal_docs = []
    for doc in documents:
        # Map to legal_documents_ai format
        legal_doc = Document(
            id=None,
            name=doc.name,
            content=doc.content,
            meta_data={
                "title": doc.name,
                "document_type": "jurisprudencia",
                "document_number": doc.meta_data.get("source", "external"),
                "year": "2024",
                "jurisdiction": "Colombia",
                "summary": doc.content[:800] if len(doc.content) > 800 else doc.content,
                "keywords": ["jurisprudencia", "corte constitucional", "external_source"],
                "tags": ["jurisprudencia", "corte constitucional", "external_source"],
                "source_url": doc.meta_data.get("source_url"),
                "status": "active"
            }
        )
        legal_docs.append(legal_doc)

    logger.info(f"Upserting {len(legal_docs)} documents into legal_documents_ai...")
    vector_db_legal.upsert(legal_docs)
    logger.info("legal_documents_ai upsert complete.")


def main():
    parser = argparse.ArgumentParser(description="Ingest external sources (Google Drive PDF + Google Sheet)")
    parser.add_argument("--drive", required=True, help="Google Drive PDF file id or full URL")
    parser.add_argument("--sheet", required=True, help="Google Sheets URL")
    args = parser.parse_args()

    if not POSTGRES_URL:
        logger.error("POSTGRES_URL not configured")
        sys.exit(1)
    if not MISTRAL_API_KEY:
        logger.error("MISTRAL_API_KEY not configured")
        sys.exit(1)

    try:
        pdf_bytes = fetch_google_drive_pdf(args.drive)
        sheet_csv = fetch_google_sheet_csv(args.sheet)
        sheet_text = csv_to_text_table(sheet_csv)
        docs = build_documents(pdf_bytes, sheet_text)
        upsert_documents(docs)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()