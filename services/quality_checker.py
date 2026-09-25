"""
Quality Checker (NLP) - ReqCraft AI
Analyzes requirements text for quality issues using spaCy + rule-based NLP:
  - Ambiguous / vague terms
  - Passive voice
  - Weak / non-testable phrasing
  - Missing "shall" in requirements
Produces a measurable quality score (0-100) and a detailed issue list.

spaCy is loaded lazily so the app still starts if the model isn't downloaded.
"""
import re

# Words/phrases that make requirements ambiguous or non-testable (IEEE quality smells)
VAGUE_TERMS = [
    "fast", "slow", "easy", "user-friendly", "user friendly", "efficient",
    "flexible", "robust", "good", "better", "best", "nice", "simple",
    "approximately", "about", "etc", "and so on", "as needed", "if possible",
    "minimal", "maximal", "optimal", "several", "some", "many", "few",
    "quickly", "easily", "appropriate", "adequate", "reasonable", "sufficient",
    "state-of-the-art", "seamless", "intuitive", "modern",
]

WEAK_WORDS = ["should", "may", "might", "could", "can", "would", "will", "ought to"]

# A sentence is treated as a *requirement* (and held to "shall") only when it
# names a system actor. This keeps descriptive prose (Purpose, Scope, References)
# from being wrongly flagged for weak wording.
ACTOR_WORDS = [
    "system", "user", "users", "application", "app", "website", "site",
    "admin", "administrator", "software", "product", "module", "component",
    "server", "database", "interface", "platform", "service", "customer",
]

_nlp = None


def _get_nlp():
    """Lazy-load spaCy. Returns None if model unavailable."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except Exception:  # noqa: BLE001
            _nlp = False  # mark as tried-and-failed
    return _nlp or None


class QualityChecker:
    def analyze(self, text: str) -> dict:
        text = (text or "").strip()
        if not text:
            return self._empty_result()

        # Strip markdown so generated (markdown) and uploaded (plain text) docs
        # are analyzed on the same footing, then keep only real sentences
        # (4+ words) — headings and fragments shouldn't count as issues or
        # inflate the denominator. This makes the score format-independent.
        clean = self._normalize(text)
        sentences = [s for s in self._split_sentences(clean) if len(s.split()) >= 4]
        issues = []

        for idx, sent in enumerate(sentences, start=1):
            issues.extend(self._check_sentence(sent, idx))

        total_sentences = max(len(sentences), 1)
        score = self._compute_score(issues, total_sentences)

        # Categorize counts
        counts = {}
        for issue in issues:
            counts[issue["type"]] = counts.get(issue["type"], 0) + 1

        return {
            "score": score,
            "grade": self._grade(score),
            "total_sentences": len(sentences),
            "total_issues": len(issues),
            "issues": issues,
            "counts": counts,
            "nlp_available": _get_nlp() is not None,
        }

    # ------------------------------------------------------------- normalization
    @staticmethod
    def _normalize(text: str) -> str:
        """Strip Markdown formatting so generated (markdown) and uploaded
        (plain-text) documents analyze identically."""
        text = re.sub(r"`+", "", text)            # inline/code fences
        text = re.sub(r"[*_]{1,3}", "", text)     # bold / italic markers
        out = []
        for line in text.split("\n"):
            line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)   # ## headings
            line = re.sub(r"^\s*[-*+]\s+", "", line)        # - bullets
            line = re.sub(r"^\s*\d+\.\s+", "", line)        # 1. list / numbering
            line = re.sub(r"^\s*>\s?", "", line)            # > blockquote
            line = line.replace("|", " ")                   # table pipes
            out.append(line)
        return "\n".join(out)

    # ----------------------------------------------------------------- checks
    def _check_sentence(self, sent: str, idx: int):
        issues = []
        lower = sent.lower()

        has_actor = any(re.search(rf"\b{a}\b", lower) for a in ACTOR_WORDS)
        has_strong = bool(re.search(r"\b(shall|must)\b", lower))

        # 1. Vague / ambiguous terms
        for term in VAGUE_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", lower):
                issues.append(self._issue(
                    "Ambiguity", "high", idx, sent,
                    f"Vague term '{term}' makes the requirement non-testable.",
                ))

        # 2. Passive voice (spaCy if available, else regex fallback)
        if self._is_passive(sent):
            issues.append(self._issue(
                "Passive Voice", "medium", idx, sent,
                "Passive voice hides the actor. Rewrite in active voice.",
            ))

        # 3. Weak modal verbs — only for actual requirements (sentences that
        #    name a system actor but use a weak modal instead of 'shall'/'must').
        #    Descriptive prose is left alone.
        if has_actor and not has_strong:
            for w in WEAK_WORDS:
                if re.search(rf"\b{re.escape(w)}\b", lower):
                    issues.append(self._issue(
                        "Weak Wording", "medium", idx, sent,
                        f"Weak word '{w}' — use 'shall' for mandatory requirements.",
                    ))
                    break

        # 4. TBD / incomplete markers
        if re.search(r"\b(tbd|to be decided|to be determined|\?\?\?)\b", lower):
            issues.append(self._issue(
                "Incompleteness", "high", idx, sent,
                "Incomplete requirement (TBD / placeholder).",
            ))

        return issues

    def _is_passive(self, sent: str) -> bool:
        nlp = _get_nlp()
        if nlp:
            doc = nlp(sent)
            return any(tok.dep_ in ("nsubjpass", "auxpass") for tok in doc)
        # Regex fallback: "is/are/was/were/be/been + past participle"
        return bool(re.search(r"\b(is|are|was|were|be|been|being)\b\s+\w+(ed|en)\b", sent.lower()))

    # ------------------------------------------------------------- scoring etc
    def _compute_score(self, issues, total_sentences) -> int:
        weight = {"high": 5, "medium": 3, "low": 1}
        cap = 6  # max penalty counted per sentence (avoids over-punishing one bad line)

        # Sum penalties per sentence, capped, so the score stays meaningful
        per_sentence = {}
        for i in issues:
            per_sentence[i["line"]] = per_sentence.get(i["line"], 0) + weight.get(i["severity"], 1)
        penalty = sum(min(p, cap) for p in per_sentence.values())

        max_penalty = total_sentences * cap
        raw = 100 - (penalty / max(max_penalty, 1)) * 100
        return max(0, min(100, round(raw)))

    def _split_sentences(self, text: str):
        nlp = _get_nlp()
        if nlp:
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents if s.text.strip()]
            if sents:
                return sents
        # Fallback splitter
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _issue(itype, severity, line, sentence, message):
        return {
            "type": itype,
            "severity": severity,
            "line": line,
            "sentence": sentence[:240],
            "message": message,
        }

    @staticmethod
    def _grade(score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 50:
            return "Fair"
        return "Poor"

    def _empty_result(self):
        return {
            "score": 0, "grade": "Poor", "total_sentences": 0,
            "total_issues": 0, "issues": [], "counts": {},
            "nlp_available": _get_nlp() is not None,
        }


quality_checker = QualityChecker()
