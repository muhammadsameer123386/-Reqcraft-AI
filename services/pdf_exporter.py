"""
PDF Exporter - ReqCraft AI
Converts a generated SRS (Markdown) into a downloadable PDF using ReportLab.
Lightweight Markdown handling (headings, bullets, paragraphs).
"""
import io
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle("H1c", parent=base["Heading1"], textColor=colors.HexColor("#4f46e5"), spaceBefore=14))
    base.add(ParagraphStyle("H2c", parent=base["Heading2"], textColor=colors.HexColor("#1e293b"), spaceBefore=10))
    base.add(ParagraphStyle("H3c", parent=base["Heading3"], textColor=colors.HexColor("#334155")))
    base.add(ParagraphStyle("Bodyc", parent=base["BodyText"], leading=15))
    return base


def markdown_to_pdf(markdown_text: str, title: str = "SRS Document") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=title,
    )
    st = _styles()
    flow = []

    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flow.append(Spacer(1, 6))
            continue

        # Inline bold -> <b>
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line.strip())
        html = html.replace("&", "&amp;").replace("&amp;lt;", "&lt;")

        if line.startswith("### "):
            flow.append(Paragraph(html[4:], st["H3c"]))
        elif line.startswith("## "):
            flow.append(Paragraph(html[3:], st["H2c"]))
        elif line.startswith("# "):
            flow.append(Paragraph(html[2:], st["H1c"]))
        elif re.match(r"^[-*]\s+", line):
            flow.append(Paragraph("&bull; " + re.sub(r"^[-*]\s+", "", html), st["Bodyc"]))
        else:
            flow.append(Paragraph(html, st["Bodyc"]))

    doc.build(flow)
    return buf.getvalue()
