"""
SRS Generator - ReqCraft AI
Generates an IEEE 830 compliant SRS document from a natural-language
project description using the Smart LLM Manager.
"""
from services.llm_manager import llm_manager
from services.ieee_validator import IEEE830Validator


SRS_PROMPT_TEMPLATE = """You are an expert Software Requirements Engineer.
Generate a complete, professional Software Requirements Specification (SRS)
document that strictly follows the IEEE 830-1998 standard structure.

PROJECT NAME: {project_name}
PROJECT DESCRIPTION:
{description}

Produce the SRS in clean Markdown using EXACTLY these top-level sections and
numbering (do not skip any section):

# Software Requirements Specification: {project_name}

## 1. Introduction
### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions, Acronyms, and Abbreviations
### 1.4 References
### 1.5 Overview

## 2. Overall Description
### 2.1 Product Perspective
### 2.2 Product Functions
### 2.3 User Characteristics
### 2.4 Constraints
### 2.5 Assumptions and Dependencies

## 3. Specific Requirements
### 3.1 Functional Requirements
(List each as FR-1, FR-2, ... with clear, testable, unambiguous statements using "shall")
### 3.2 Non-Functional Requirements
(Performance, Security, Usability, Reliability — list as NFR-1, NFR-2, ...)
### 3.3 External Interface Requirements
### 3.4 System Features

## 4. Appendices

RULES:
- Write specific, testable requirements. Avoid vague words like "fast", "easy", "user-friendly", "etc.".
- Every functional requirement MUST use the word "shall".
- Be concrete and detailed based on the project description.
- Output ONLY the Markdown SRS, no extra commentary.
"""


class SRSGenerator:
    def generate(self, project_name: str, description: str):
        """Returns dict: {markdown, provider, compliance, success, error}."""
        prompt = SRS_PROMPT_TEMPLATE.format(
            project_name=project_name.strip() or "Untitled Project",
            description=description.strip(),
        )
        result = llm_manager.generate(prompt, temperature=0.4)

        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "markdown": "",
                "provider": result.provider,
                "compliance": None,
            }

        markdown = result.text
        # Immediately score the generated SRS for IEEE 830 compliance
        compliance = IEEE830Validator().validate(markdown)

        return {
            "success": True,
            "error": "",
            "markdown": markdown,
            "provider": result.provider,
            "compliance": compliance,
        }


srs_generator = SRSGenerator()
