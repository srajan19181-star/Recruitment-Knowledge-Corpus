"""
Deterministic recruitment compliance and job ad drafting tools.

Provides verifiable, rule-based verification against pay transparency
and fair hiring mandates (NYC, CA, CO, WA, etc.) as well as standardized,
bias-reduced job ad generation.
"""

import re
from typing import Any

# Regex patterns for salary ranges and hourly rates
SALARY_PATTERNS = [
    re.compile(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:-|–|to)\s*\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?", re.I),
    re.compile(r"\$\s*\d{2,3}(?:k)?\s*(?:-|–|to)\s*\$?\s*\d{2,3}(?:k)?", re.I),
    re.compile(r"\$\s*\d{2,3}(?:\.\d{2})?\s*(?:/hr|per hour|an hour)", re.I),
    re.compile(r"\b\d{2,3},\d{3}\s*(?:-|–|to)\s*\d{2,3},\d{3}\s*(?:usd|dollars)?\b", re.I),
]

# Prohibited salary history inquiries
SALARY_HISTORY_PATTERN = re.compile(
    r"\b(salary history|previous salary|current salary|past compensation|prior earnings|what do you currently make)\b",
    re.I,
)

# Biased or exclusionary terminology
AGE_BIAS_PATTERNS = [
    re.compile(r"\b(recent graduate|recent grad|young professional|digital native|energetic youth)\b", re.I),
    re.compile(r"\b(maximum \d+ years|no more than \d+ years of experience)\b", re.I),
]

MASCULINE_CODED_PATTERNS = [
    re.compile(r"\b(rockstar|ninja|crush it|dominate|killer developer|alpha)\b", re.I),
]

MANDATORY_PAY_TRANSPARENCY_JURISDICTIONS = {
    "nyc": "New York City (Local Law 32)",
    "ny": "New York State (Labor Law § 194-b)",
    "new york": "New York State / NYC",
    "co": "Colorado (Equal Pay for Equal Work Act)",
    "colorado": "Colorado (Equal Pay for Equal Work Act)",
    "ca": "California (SB 1162)",
    "california": "California (SB 1162)",
    "wa": "Washington State (Equal Pay and Opportunities Act)",
    "washington": "Washington State (Equal Pay and Opportunities Act)",
}


def check_ad_compliance(ad_text: str, jurisdiction: str) -> dict[str, Any]:
    """Evaluates job posting text against statutory compliance rules."""
    norm_jurisdiction = jurisdiction.strip().lower()
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    has_salary = any(pat.search(ad_text) for pat in SALARY_PATTERNS)

    # Check pay transparency mandate
    if norm_jurisdiction in MANDATORY_PAY_TRANSPARENCY_JURISDICTIONS:
        statute = MANDATORY_PAY_TRANSPARENCY_JURISDICTIONS[norm_jurisdiction]
        if not has_salary:
            violations.append(
                f"Missing mandatory base salary or hourly wage range required under {statute}."
            )
        else:
            recommendations.append(
                f"Compliant salary disclosure detected for {statute}."
            )

        # Colorado specific benefits disclosure
        if norm_jurisdiction in {"co", "colorado"}:
            benefits_detected = bool(re.search(r"\b(health|medical|401k|dental|benefits|bonus)\b", ad_text, re.I))
            if not benefits_detected:
                violations.append(
                    "Colorado law requires a general description of all employment benefits and incentive compensation."
                )

    # Check salary history bans
    if SALARY_HISTORY_PATTERN.search(ad_text):
        violations.append(
            "Prohibited inquiry: Requesting prior or current salary history violates salary history ban legislation."
        )

    # Check age bias indicators
    for pat in AGE_BIAS_PATTERNS:
        match = pat.search(ad_text)
        if match:
            warnings.append(
                f"Potentially age-discriminatory phrasing: '{match.group(0)}'. Use skill-based qualifications instead."
            )

    # Check aggressive/masculine-coded jargon
    for pat in MASCULINE_CODED_PATTERNS:
        match = pat.search(ad_text)
        if match:
            warnings.append(
                f"Exclusionary jargon detected: '{match.group(0)}'. Consider collaborative, objective alternatives."
            )

    # EOE Statement check
    if not re.search(r"\b(equal opportunity employer|eoe|equal opportunity|without regard to)\b", ad_text, re.I):
        recommendations.append(
            "Add an Equal Employment Opportunity (EEO) commitment statement."
        )

    return {
        "compliant": len(violations) == 0,
        "jurisdiction": jurisdiction,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def draft_job_ad(
    role: str,
    level: str,
    location: str,
    salary_range: str,
    must_haves: list[str],
) -> dict[str, Any]:
    """Generates an inclusive, compliant job advertisement template."""
    skills_bullets = "\n".join(f"- {skill.strip()}" for skill in must_haves if skill.strip())

    ad_markdown = f"""# {role} ({level})

**Location:** {location}
**Compensation:** {salary_range} (Base Salary / Range)
**Employment Type:** Full-time

## About the Role
We are seeking a thoughtful {role} at the {level} level to join our team. In this position, you will contribute directly to core product initiatives, collaborate with cross-functional partners, and build scalable, user-focused systems.

## Key Responsibilities
- Design, implement, and maintain high-reliability services and user-facing workflows.
- Partner with product managers and engineers to define technical scope and roadmap priorities.
- Champion sound engineering fundamentals, automated testing, and comprehensive system observability.

## Qualifications & Must-Haves
{skills_bullets}

## Compensation & Benefits
- **Base Range:** {salary_range} (commensurate with experience and geographic location).
- Comprehensive health, dental, and vision insurance options.
- 401(k) retirement plan with company match.
- Flexible paid time off and designated company holidays.

## Equal Opportunity Employer
We are committed to building an inclusive and diverse workplace. All qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, disability, or protected veteran status.
"""

    return {
        "role": role,
        "level": level,
        "location": location,
        "salary_range": salary_range,
        "ad_markdown": ad_markdown.strip(),
        "compliance_notes": [
            "Good-faith salary range explicitly included.",
            "Objective, competency-based requirements without restrictive year caps.",
            "Standard Equal Opportunity Employer (EOE) statement incorporated.",
        ],
    }
