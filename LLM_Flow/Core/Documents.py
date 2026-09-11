import re
import sqlite3
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF


class KnowledgeBase:

    def __init__(
        self,
        db_path="Knowledge/knowledge.db",
        document_folder="Knowledge/Documents"
    ):
        self.db_path = Path(db_path)
        self.document_folder = Path(document_folder)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.document_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.create_database()

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    def create_database(self):

        with sqlite3.connect(self.db_path) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    path TEXT,
                    added_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    chunk_index INTEGER,
                    content TEXT,

                    FOREIGN KEY(document_id)
                    REFERENCES documents(id)
                )
            """)

            conn.commit()

    # --------------------------------------------------
    # TEXT EXTRACTION
    # --------------------------------------------------

    def extract_text(self, path: Path) -> str:

        suffix = path.suffix.lower()

        if suffix in [".txt", ".md"]:

            return path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        if suffix == ".pdf":

            document = fitz.open(path)

            pages = []

            for page in document:
                pages.append(
                    page.get_text()
                )

            document.close()

            return "\n".join(pages)

        raise ValueError(
            f"Unsupported document type: {suffix}"
        )

    # --------------------------------------------------
    # CHUNK DOCUMENT
    # --------------------------------------------------

    def chunk_text(
        self,
        text: str,
        chunk_size=1500
    ) -> list[str]:

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        chunks = []

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end]

            chunks.append(chunk)

            start = end

        return chunks

    # --------------------------------------------------
    # INGEST DOCUMENT
    # --------------------------------------------------

    def ingest_document(
        self,
        file_path
    ):

        path = Path(file_path).resolve()

        text = self.extract_text(path)

        chunks = self.chunk_text(text)

        with sqlite3.connect(self.db_path) as conn:

            # Remove old version if already ingested
            existing = conn.execute(
                """
                SELECT id
                FROM documents
                WHERE filename = ?
                """,
                (path.name,)
            ).fetchone()

            if existing:

                document_id = existing[0]

                conn.execute(
                    """
                    DELETE FROM chunks
                    WHERE document_id = ?
                    """,
                    (document_id,)
                )

                conn.execute(
                    """
                    UPDATE documents
                    SET path = ?, added_at = ?
                    WHERE id = ?
                    """,
                    (
                        str(path),
                        datetime.now().isoformat(),
                        document_id
                    )
                )

            else:

                cursor = conn.execute(
                    """
                    INSERT INTO documents
                    (
                        filename,
                        path,
                        added_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        path.name,
                        str(path),
                        datetime.now().isoformat()
                    )
                )

                document_id = cursor.lastrowid

            for i, chunk in enumerate(chunks):

                conn.execute(
                    """
                    INSERT INTO chunks
                    (
                        document_id,
                        chunk_index,
                        content
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        document_id,
                        i,
                        chunk
                    )
                )

            conn.commit()

        return {
            "filename": path.name,
            "chunks": len(chunks)
        }

    # --------------------------------------------------
    # INGEST ENTIRE FOLDER
    # --------------------------------------------------

    def ingest_folder(self):

        results = []

        for path in self.document_folder.iterdir():

            if path.suffix.lower() not in [
                ".pdf",
                ".txt",
                ".md"
            ]:
                continue

            try:

                result = self.ingest_document(
                    path
                )

                results.append(result)

            except Exception as error:

                results.append({
                    "filename": path.name,
                    "error": str(error)
                })

        return results

    # --------------------------------------------------
    # SIMPLE LOCAL SEARCH
    # --------------------------------------------------

    def search(
        self,
        query: str,
        top_k=5
    ):

        query_words = set(
            re.findall(
                r"[a-zA-Z0-9_-]+",
                query.lower()
            )
        )

        with sqlite3.connect(self.db_path) as conn:

            rows = conn.execute("""
                SELECT
                    documents.filename,
                    chunks.chunk_index,
                    chunks.content

                FROM chunks

                JOIN documents
                ON chunks.document_id = documents.id
            """).fetchall()

        ranked = []

        for filename, chunk_index, content in rows:

            content_words = set(
                re.findall(
                    r"[a-zA-Z0-9_-]+",
                    content.lower()
                )
            )

            common = query_words.intersection(
                content_words
            )

            if not common:
                continue

            score = len(common) / max(
                len(query_words),
                1
            )

            ranked.append({
                "filename": filename,
                "chunk": chunk_index,
                "score": round(score, 3),
                "content": content
            })

        ranked.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return ranked[:top_k]

    # --------------------------------------------------
    # READ EXACT DOCUMENT
    # --------------------------------------------------

    def read_document(
        self,
        filename: str
    ):

        with sqlite3.connect(self.db_path) as conn:

            row = conn.execute(
                """
                SELECT path
                FROM documents
                WHERE filename = ?
                """,
                (filename,)
            ).fetchone()

        if not row:

            raise FileNotFoundError(
                f"{filename} is not in the knowledge base."
            )

        return self.extract_text(
            Path(row[0])
        )