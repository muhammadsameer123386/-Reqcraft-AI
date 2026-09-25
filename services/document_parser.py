"""
Document Parser - ReqCraft AI
Extracts plain text from uploaded SRS files (PDF / DOCX / TXT) for the
Upload Analysis feature (basic analysis in FYP-1).
"""
import os
import re


def markdownify_srs(text: str) -> str:
    """Heuristically turn plain extracted SRS text into Markdown so an uploaded
    document renders with the same styled headings/sections as a generated SRS.

    - "1. Introduction"  -> "## 1. Introduction"
    - "1.1 Purpose"      -> "### 1.1 Purpose"
    - ALL-CAPS short line -> "## ..." (section title)
    - "FR-1 ..." / "NFR-1 ..." -> bold list item
    Requirement sentences (long, end with '.', contain shall/must) are left as-is.
    """
    if not text:
        return ""

    out = []
    title_done = False
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            out.append("")
            continue
        # Already a Markdown heading — keep it
        if line.startswith("#"):
            out.append(line)
            title_done = True
            continue

        words = line.split()
        is_sentence = (
            line.endswith((".", ";", ":"))
            or len(words) > 9
            or re.search(r"\b(shall|must|will|should)\b", line, re.I)
        )

        # Numbered headings: "1", "1.1", "1.1.1" + a short title (not a sentence)
        m = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", line)
        if m and not is_sentence:
            level = min(m.group(1).count(".") + 2, 5)   # 1->##, 1.1->###
            out.append(f"{'#' * level} {line}")
            title_done = True
            continue

        # FR-1 / NFR-1 style requirement identifiers -> bold list item
        fr = re.match(r"^((?:FR|NFR|RQ|REQ)[-\s]?\d+)[\.\):\s]+(.+)$", line, re.I)
        if fr:
            out.append(f"- **{fr.group(1).upper().replace(' ', '-')}** {fr.group(2)}")
            continue

        # ALL-CAPS short standalone line -> section heading
        if line.isupper() and 1 <= len(words) <= 8 and any(c.isalpha() for c in line):
            out.append(f"## {line}")
            title_done = True
            continue

        # First meaningful line that isn't a section -> document title
        if not title_done:
            out.append(f"# {line}")
            title_done = True
            continue

        out.append(line)

    return "\n".join(out)


class DocumentParser:
    def extract_text(self, filepath: str) -> str:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            return self._from_pdf(filepath)
        if ext == ".docx":
            return self._from_docx(filepath)
        if ext == ".txt":
            return self._from_txt(filepath)
        raise ValueError(f"Unsupported file type: {ext}")

    def _from_pdf(self, filepath: str) -> str:
        import pdfplumber
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text).strip()

    def _from_docx(self, filepath: str) -> str:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    def _from_txt(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()


document_parser = DocumentParser()
