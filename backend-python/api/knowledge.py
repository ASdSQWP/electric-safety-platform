"""知识库 — 向量存储、文档切片、语义检索"""

from fastapi import APIRouter, File, Query, UploadFile
from pydantic import BaseModel

router = APIRouter()


# ── Pydantic models ──────────────────────────────────────────────

class SearchResult(BaseModel):
    document_id: str
    title: str
    content_snippet: str
    score: float
    category: str = ""
    chunk_index: int = 0


class UploadResponse(BaseModel):
    document_id: str
    title: str
    category: str
    chunk_count: int
    status: str


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    category: str
    chunk_count: int


# ── 辅助函数 ─────────────────────────────────────────────────────

async def _get_kb():
    from services.knowledge_service import KnowledgeService

    return KnowledgeService()


def _extract_text(file_content: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if filename else "txt"
    if ext == "pdf":
        import fitz

        doc = fitz.open(stream=file_content, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
    elif ext in ("docx", "doc"):
        import tempfile

        from docx import Document

        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(file_content)
            tmp.flush()
            doc = Document(tmp.name)
            text = "\n".join(p.text for p in doc.paragraphs)
    else:
        text = file_content.decode("utf-8", errors="ignore")
    return text


# ── 端点 ──────────────────────────────────────────────────────────

@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), category: str = "施工规范"):
    """上传知识库文档，自动切片→向量化→存入ChromaDB"""
    content = await file.read()
    text = _extract_text(content, file.filename or "unknown")
    if not text.strip():
        return UploadResponse(
            document_id=file.filename or "unknown",
            title=file.filename or "unknown",
            category=category,
            chunk_count=0,
            status="文档内容为空",
        )

    kb = await _get_kb()
    doc_id = file.filename or "unknown"
    await kb.delete_document(doc_id)
    count = await kb.add_document(doc_id, file.filename or "unknown", category, text)

    return UploadResponse(
        document_id=doc_id,
        title=file.filename or "unknown",
        category=category,
        chunk_count=count,
        status="已向量化" if count > 0 else "向量化失败",
    )


@router.get("/search", response_model=list[SearchResult])
async def search_knowledge(
    query: str = Query(...),
    top_k: int = Query(5, ge=1, le=50),
    category: str | None = Query(None),
    threshold: float = Query(0.5, ge=0, le=1.0),
):
    """语义检索知识库"""
    kb = await _get_kb()
    return await kb.search(query=query, top_k=top_k, category=category, threshold=threshold)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """删除知识库中文档的所有切片"""
    kb = await _get_kb()
    removed = await kb.delete_document(document_id)
    return {"document_id": document_id, "removed_chunks": removed, "status": "已删除"}


@router.get("/documents", response_model=list[DocumentSummary])
async def list_documents():
    """列出所有已索引文档"""
    kb = await _get_kb()
    return await kb.get_documents()


@router.get("/categories")
async def list_categories():
    """列出知识库统计信息"""
    kb = await _get_kb()
    stats = await kb.get_statistics()
    return {
        "categories": [
            {"name": "施工规范", "value": "construction"},
            {"name": "安全规程", "value": "safety"},
            {"name": "历史案例", "value": "history"},
        ],
        "statistics": stats,
    }
