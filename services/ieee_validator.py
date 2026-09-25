"""
IEEE 830 Compliance Validator - ReqCraft AI
Checks an SRS document (Markdown or plain text) against the IEEE 830-1998
section structure and returns a section-wise compliance score (0-100) plus a
list of missing sections.
"""
import re


# Canonical IEEE 830-1998 sections with keyword variants for matching
IEEE_830_SECTIONS = [
    ("Introduction", ["introduction"]),
    ("Purpose", ["purpose"]),
    ("Scope", ["scope"]),
    ("Definitions / Acronyms", ["definition", "acronym", "abbreviation"]),
    ("References", ["reference"]),
    ("Overview", ["overview"]),
    ("Overall Description", ["overall description"]),
    ("Product Perspective", ["product perspective"]),
    ("Product Functions", ["product function"]),
    ("User Characteristics", ["user characteristic"]),
    ("Constraints", ["constraint"]),
    ("Assumptions and Dependencies", ["assumption", "dependenc"]),
    ("Specific Requirements", ["specific requirement"]),
    ("Functional Requirements", ["functional requirement"]),
    ("Non-Functional Requirements", ["non-functional", "nonfunctional", "non functional"]),
    ("External Interface Requirements", ["external interface", "interface requirement"]),
]


class IEEE830Validator:
    def validate(self, text: str) -> dict:
        lower = (text or "").lower()
        sections = []
        present_count = 0

        for name, keywords in IEEE_830_SECTIONS:
            found = any(kw in lower for kw in keywords)
            if found:
                present_count += 1
            sections.append({"section": name, "present": found})

        total = len(IEEE_830_SECTIONS)
        score = round((present_count / total) * 100)
        missing = [s["section"] for s in sections if not s["present"]]

        # Bonus check: are requirements actually written with "shall"?
        shall_count = len(re.findall(r"\bshall\b", lower))
        fr_count = len(re.findall(r"\bfr[-\s]?\d+", lower))

        return {
            "score": score,
            "present": present_count,
            "total": total,
            "sections": sections,
            "missing": missing,
            "shall_count": shall_count,
            "requirement_count": fr_count,
            "grade": self._grade(score),
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
