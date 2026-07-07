"""Source loaders: turn (source_type, content) into plain text.

All heavy libraries (pypdf, python-docx, pandas, httpx, bs4) are imported
lazily; every loader has a best-effort fallback so ingestion never crashes.
"""
from __future__ import annotations

import io
import json
import re
from typing import Union

Content = Union[bytes, str]


def _to_bytes(content: Content) -> bytes:
    return content.encode("utf-8", errors="replace") if isinstance(content, str) else content


def _to_text(content: Content) -> str:
    return content if isinstance(content, str) else content.decode("utf-8", errors="replace")


def _load_pdf(content: Content) -> str:
    try:
        from pypdf import PdfReader  # lazy

        reader = PdfReader(io.BytesIO(_to_bytes(content)))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return _to_text(content)


def _load_docx(content: Content) -> str:
    try:
        import docx  # lazy (python-docx)

        d = docx.Document(io.BytesIO(_to_bytes(content)))
        return "\n".join(p.text for p in d.paragraphs if p.text)
    except Exception:
        return _to_text(content)


def _load_tabular(content: Content, kind: str) -> str:
    try:
        import pandas as pd  # lazy

        buf = io.BytesIO(_to_bytes(content))
        df = pd.read_excel(buf) if kind == "xlsx" else pd.read_csv(buf)
        rows = []
        for _, row in df.iterrows():
            rows.append("; ".join(f"{c}: {row[c]}" for c in df.columns))
        return "\n".join(rows)
    except Exception:
        return _to_text(content)


def _strip_html(html: str) -> str:
    try:
        from bs4 import BeautifulSoup  # lazy

        soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return re.sub(r"\n{3,}", "\n\n", soup.get_text("\n")).strip()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)


def _has_lxml() -> bool:
    try:
        import lxml  # noqa: F401

        return True
    except Exception:
        return False


def _load_url(url: str) -> str:
    try:
        import httpx  # lazy

        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        return _strip_html(resp.text)
    except Exception:
        return f"[unfetchable url] {url}"


def _load_faq(content: Content) -> str:
    """FAQ format: JSON list of {question, answer} or 'Q:/A:' plain text."""
    text = _to_text(content)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return "\n\n".join(
                f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
                for item in data if isinstance(item, dict)
            )
    except Exception:
        pass
    return text


def load_source(source_type: str, content: Content) -> str:
    """Dispatch on source_type → plain text."""
    st = (source_type or "text").lower()
    if st == "pdf":
        return _load_pdf(content)
    if st in ("docx", "doc"):
        return _load_docx(content)
    if st == "csv":
        return _load_tabular(content, "csv")
    if st in ("xlsx", "xls", "excel"):
        return _load_tabular(content, "xlsx")
    if st == "url":
        return _load_url(_to_text(content).strip())
    if st in ("html", "htm"):
        return _strip_html(_to_text(content))
    if st == "faq":
        return _load_faq(content)
    return _to_text(content)  # plain text / markdown / unknown
