from app.tools import check_ad_compliance, draft_job_ad


def test_compliance_detects_missing_salary_for_nyc():
    ad = "We are seeking a Software Engineer to join our team in New York City."
    result = check_ad_compliance(ad, "nyc")
    assert result["compliant"] is False
    assert any("Missing mandatory base salary" in v for v in result["violations"])


def test_compliance_passes_with_salary_range_for_nyc():
    ad = "Software Engineer in NYC. Base salary range: $130,000 - $160,000 per year. Equal Opportunity Employer."
    result = check_ad_compliance(ad, "nyc")
    assert result["compliant"] is True
    assert len(result["violations"]) == 0


def test_compliance_flags_salary_history():
    ad = "Candidates must provide past compensation and salary history."
    result = check_ad_compliance(ad, "california")
    assert any("salary history" in v.lower() for v in result["violations"])


def test_compliance_flags_colorado_benefits_omission():
    ad = "Remote role for Colorado applicants. Compensation: $110,000 - $130,000."
    result = check_ad_compliance(ad, "colorado")
    assert any("benefits" in v.lower() for v in result["violations"])


def test_draft_job_ad_structure():
    res = draft_job_ad(
        role="Frontend Engineer",
        level="Senior",
        location="Remote (US)",
        salary_range="$140,000 - $175,000",
        must_haves=["5+ years TypeScript", "React App Router experience"],
    )
    assert res["role"] == "Frontend Engineer"
    assert "$140,000 - $175,000" in res["ad_markdown"]
    assert "5+ years TypeScript" in res["ad_markdown"]
    assert "Equal Opportunity Employer" in res["ad_markdown"]
