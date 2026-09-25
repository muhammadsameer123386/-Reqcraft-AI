# ReqCraft AI — AI-Based SRS Generator & Quality Checker

**FYP-1** · Artificial Intelligence & Natural Language Processing
Emaan Institute of Management & Sciences — Batch Fall-2023

ReqCraft AI is an intelligent in-house tool that automates **IEEE 830** compliant SRS
document generation, performs **NLP-based quality checking**, and analyzes existing SRS
uploads — powered by a **Smart LLM Manager** with automatic fallback.

---

## ✨ Features (FYP-1)

| Feature | Description |
|---|---|
| 🪄 **SRS Generation** | Natural-language description → full IEEE 830 SRS (Markdown) |
| 🛡️ **Quality Checking** | NLP detects ambiguity, vague terms, passive voice, weak wording (score 0–100) |
| ✅ **IEEE 830 Compliance** | Section-wise compliance scoring + missing-section detection |
| ☁️ **Upload Analysis** | Upload PDF/DOCX/TXT → instant compliance + quality report |
| 📄 **PDF Export** | Download generated SRS as a formatted PDF |

## 🤖 Smart LLM Manager (auto-fallback)

```
Google Gemini  (PRIMARY)  →  HuggingFace  (FALLBACK)  →  Ollama  (LOCAL BACKUP)
```

If a provider fails (quota / network / missing key), the manager automatically
switches to the next one — so generation always works.

## 🧱 Tech Stack

- **Backend:** Python · Flask · Flask-SQLAlchemy · Flask-Login · SQLite
- **LLM:** google-generativeai (Gemini) · HuggingFace Inference API · Ollama
- **NLP:** spaCy (`en_core_web_sm`)
- **Docs:** pdfplumber · python-docx · ReportLab
- **Frontend:** Bootstrap 5 · Bootstrap Icons · custom CSS design system

---

## 🚀 Setup

### 1. Install dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure API keys
```powershell
copy .env.example .env
```
Then edit `.env` and add your free API keys:
- **Gemini:** https://aistudio.google.com/apikey
- **HuggingFace:** https://huggingface.co/settings/tokens

> The app still runs without keys (Quality Checker, Upload Analysis, IEEE validation
> work fully offline). Only AI generation needs a key.

### 3. Run
```powershell
python app.py
```
Open **http://localhost:5000**

---

## 📁 Project Structure

```
fyp-1/
├── app.py                 # Flask app factory + entry point
├── config.py              # Configuration (env-driven)
├── requirements.txt
├── models/
│   └── database.py        # User + SRSDocument models
├── services/
│   ├── llm_manager.py     # Smart LLM Manager (Gemini→HF→Ollama)
│   ├── srs_generator.py   # IEEE 830 SRS generation
│   ├── quality_checker.py # NLP quality analysis
│   ├── ieee_validator.py  # IEEE 830 compliance scoring
│   ├── document_parser.py # PDF/DOCX/TXT extraction
│   └── pdf_exporter.py    # Markdown → PDF
├── routes/
│   ├── auth.py            # Register / Login / Logout
│   └── main.py            # Dashboard, generate, quality, upload, export
├── templates/             # Bootstrap 5 UI
└── static/                # CSS design system + JS
```

## 👥 Team
- Muhammad Sameer · Hammad Khan · Sudais
- **Supervisor:** Sir Asfand Yar · **Co-Supervisor:** Sir Umer
