import hashlib
import os
import re

from config import settings


class KnowledgeService:
    """RAG管道：文档切片→向量化→ChromaDB存储→语义检索"""

    EMBEDDING_MODEL = getattr(settings, "embedding_model", "paraphrase-multilingual-MiniLM-L12-v2")
    CHROMA_DIR = getattr(settings, "chroma_db_dir", "./chroma_db")
    COLLECTION = "esafety_knowledge"

    def __init__(self):
        self._embedder = None
        self._client = None

    async def _ensure_init(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(self.EMBEDDING_MODEL)
        if self._client is None:
            import chromadb

            os.makedirs(self.CHROMA_DIR, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.CHROMA_DIR)

    async def _collection(self):
        await self._ensure_init()
        return self._client.get_or_create_collection(self.COLLECTION)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """按段落+字符数切片，相邻块有重叠"""
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) > chunk_size and current:
                chunks.append(current.strip())
                current = current[-overlap:] + para if overlap else para
            else:
                current = current + "\n" + para if current else para
        if current.strip():
            chunks.append(current.strip())
        return chunks or [text[:chunk_size]]

    async def add_document(self, document_id: str, title: str, category: str, text: str) -> int:
        """切片、向量化并存入ChromaDB，返回块数量"""
        coll = await self._collection()
        chunks = self.chunk_text(text)
        if not chunks:
            return 0

        embeddings = self._embedder.encode(chunks, show_progress_bar=False).tolist()
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": document_id, "title": title, "category": category, "chunk_index": i}
            for i in range(len(chunks))
        ]

        coll.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        return len(chunks)

    async def search(
        self, query: str, top_k: int = 5, category: str | None = None, threshold: float = 0.5
    ) -> list[dict]:
        """语义检索，返回 {document_id, title, content_snippet, score, category, chunk_index}"""
        coll = await self._collection()
        query_embedding = self._embedder.encode([query], show_progress_bar=False).tolist()

        where_filter = {"category": category} if category else None
        results = coll.query(query_embeddings=query_embedding, n_results=top_k, where=where_filter)

        items = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                score = 1 - results["distances"][0][i] if results["distances"] else 0
                if score < threshold:
                    continue
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                items.append(
                    {
                        "document_id": meta.get("document_id", ""),
                        "title": meta.get("title", ""),
                        "content_snippet": (results["documents"][0][i][:300] if results["documents"] else ""),
                        "score": round(score, 4),
                        "category": meta.get("category", ""),
                        "chunk_index": meta.get("chunk_index", 0),
                    }
                )
        return items

    async def delete_document(self, document_id: str) -> int:
        """删除文档的所有块"""
        coll = await self._collection()
        existing = coll.get(where={"document_id": document_id})
        if existing and existing["ids"]:
            coll.delete(ids=existing["ids"])
            return len(existing["ids"])
        return 0

    async def get_documents(self) -> list[dict]:
        """列出所有已索引文档的摘要"""
        coll = await self._collection()
        result = coll.get()
        docs: dict[str, dict] = {}
        if result["metadatas"]:
            for meta in result["metadatas"]:
                did = meta.get("document_id", "")
                if did not in docs:
                    docs[did] = {
                        "document_id": did,
                        "title": meta.get("title", ""),
                        "category": meta.get("category", ""),
                        "chunk_count": 1,
                    }
                else:
                    docs[did]["chunk_count"] += 1
        return list(docs.values())

    async def get_statistics(self) -> dict:
        """知识库统计"""
        coll = await self._collection()
        result = coll.get()
        total_chunks = len(result["ids"]) if result["ids"] else 0
        categories: dict[str, int] = {}
        if result["metadatas"]:
            for meta in result["metadatas"]:
                cat = meta.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
        doc_ids = set(m.get("document_id", "") for m in (result["metadatas"] or []))
        return {
            "document_count": len(doc_ids),
            "chunk_count": total_chunks,
            "categories": categories,
        }
