"""
Main Routes - ReqCraft AI
Landing, dashboard, SRS generation, quality checking, upload analysis,
document view, and PDF export.
"""
import os
import uuid

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, send_file, abort, Response,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models.database import db, SRSDocument
from services.srs_generator import srs_generator
from services.quality_checker import quality_checker
from services.ieee_validator import IEEE830Validator
from services.document_parser import document_parser, markdownify_srs
from services.pdf_exporter import markdown_to_pdf
from services.llm_manager import llm_manager

main_bp = Blueprint("main", __name__)


def _allowed(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# --------------------------------------------------------------------- public
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


# ------------------------------------------------------------------ dashboard
@main_bp.route("/dashboard")
@login_required
def dashboard():
    docs = SRSDocument.query.filter_by(user_id=current_user.id) \
        .order_by(SRSDocument.created_at.desc()).all()

    stats = {
        "total": len(docs),
        "generated": sum(1 for d in docs if d.source == "generated"),
        "uploaded": sum(1 for d in docs if d.source == "uploaded"),
        "avg_compliance": round(sum(d.compliance_score for d in docs) / len(docs)) if docs else 0,
    }
    return render_template("dashboard.html", docs=docs, stats=stats,
                           providers=llm_manager.provider_status())


# -------------------------------------------------------------- SRS generation
@main_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    if request.method == "POST":
        project_name = request.form.get("project_name", "").strip()
        description = request.form.get("description", "").strip()

        if not description:
            flash("Please enter a project description.", "danger")
            return render_template("generate.html")

        result = srs_generator.generate(project_name, description)
        if not result["success"]:
            flash(f"Generation failed: {result['error']}", "danger")
            return render_template("generate.html",
                                   project_name=project_name, description=description)

        # Quality score on generated content
        quality = quality_checker.analyze(result["markdown"])

        doc = SRSDocument(
            user_id=current_user.id,
            project_name=project_name or "Untitled Project",
            description=description,
            content=result["markdown"],
            source="generated",
            provider=result["provider"],
            compliance_score=result["compliance"]["score"],
            quality_score=quality["score"],
        )
        db.session.add(doc)
        db.session.commit()
        flash(f"SRS generated via {result['provider']}!", "success")
        return redirect(url_for("main.view_document", doc_id=doc.id))

    return render_template("generate.html")


# --------------------------------------------------------- quality checker tool
@main_bp.route("/quality", methods=["GET", "POST"])
@login_required
def quality():
    report = None
    text = ""
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Please paste some requirements text to analyze.", "danger")
        else:
            report = quality_checker.analyze(text)
    return render_template("quality.html", report=report, text=text)


# ------------------------------------------------------------- upload analysis
@main_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    analysis = None
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return render_template("upload.html")

        if not _allowed(file.filename):
            flash("Unsupported file type. Allowed: PDF, DOCX, TXT.", "danger")
            return render_template("upload.html")

        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(path)

        try:
            text = document_parser.extract_text(path)
        except Exception as e:  # noqa: BLE001
            flash(f"Could not read file: {e}", "danger")
            return render_template("upload.html")
        finally:
            if os.path.exists(path):
                os.remove(path)

        if not text.strip():
            flash("No readable text found in the document.", "warning")
            return render_template("upload.html")

        # Basic upload analysis (FYP-1): IEEE 830 compliance + quality check
        compliance = IEEE830Validator().validate(text)
        quality_report = quality_checker.analyze(text)

        doc = SRSDocument(
            user_id=current_user.id,
            project_name=secure_filename(file.filename),
            description="Uploaded document",
            content=text,
            source="uploaded",
            provider="n/a",
            compliance_score=compliance["score"],
            quality_score=quality_report["score"],
        )
        db.session.add(doc)
        db.session.commit()

        analysis = {
            "filename": file.filename,
            "compliance": compliance,
            "quality": quality_report,
            "word_count": len(text.split()),
            "doc_id": doc.id,
        }
        flash("Document analyzed successfully!", "success")

    return render_template("upload.html", analysis=analysis)


# ---------------------------------------------------------------- view / export
@main_bp.route("/document/<int:doc_id>")
@login_required
def view_document(doc_id):
    doc = db.session.get(SRSDocument, doc_id)
    if not doc or doc.user_id != current_user.id:
        abort(404)

    compliance = IEEE830Validator().validate(doc.content or "")
    quality = quality_checker.analyze(doc.content or "")

    # Self-heal: keep the stored scores in sync with the current analysis so the
    # dashboard and this view never disagree (e.g. after a scoring-logic change).
    if doc.quality_score != quality["score"] or doc.compliance_score != compliance["score"]:
        doc.quality_score = quality["score"]
        doc.compliance_score = compliance["score"]
        db.session.commit()

    # Generated docs are already Markdown; uploaded docs are plain extracted
    # text — convert them to Markdown so both render with the same styling.
    render_content = doc.content or ""
    if doc.source == "uploaded":
        render_content = markdownify_srs(render_content)

    return render_template("document.html", doc=doc, render_content=render_content,
                           compliance=compliance, quality=quality)


@main_bp.route("/document/<int:doc_id>/export")
@login_required
def export_pdf(doc_id):
    doc = db.session.get(SRSDocument, doc_id)
    if not doc or doc.user_id != current_user.id:
        abort(404)

    # Uploaded docs are plain extracted text — markdownify so the PDF renders
    # with the same styled headings/sections as a generated SRS.
    content = doc.content or ""
    if doc.source == "uploaded":
        content = markdownify_srs(content)

    pdf_bytes = markdown_to_pdf(content, title=doc.project_name)
    safe = secure_filename(doc.project_name) or "srs_document"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe}.pdf"},
    )


@main_bp.route("/document/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document(doc_id):
    doc = db.session.get(SRSDocument, doc_id)
    if not doc or doc.user_id != current_user.id:
        abort(404)
    db.session.delete(doc)
    db.session.commit()
    flash("Document deleted.", "info")
    return redirect(url_for("main.dashboard"))


# --------------------------------------------------------------------- JSON API
@main_bp.route("/api/quality", methods=["POST"])
@login_required
def api_quality():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    return jsonify(quality_checker.analyze(text))
