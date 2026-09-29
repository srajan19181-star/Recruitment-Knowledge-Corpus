"""
Generates the recruitment and job ad compliance corpus PDFs.
Each document contains structured, multi-page professional recruitment guides.
Compliance documents contain explicit statutory disclaimer notices.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak


DISCLAIMER = (
    "<b>Legal Notice:</b> This document is an informational summary, not legal advice. "
    "Statutory mandates vary and evolve; please verify all policies against official governmental and legal sources."
)


DOCUMENTS = [
    {
        "filename": "pay_transparency_nyc.pdf",
        "title": "New York City Pay Transparency Compliance Guide (Local Law 32)",
        "is_compliance": True,
        "sections": [
            (
                "Overview and Scope",
                "New York City Local Law 32 of 2022 amends the New York City Human Rights Law (NYCHRL) to require "
                "employers advertising jobs in New York City to state the minimum and maximum annual salary or hourly wage "
                "for the position. The law applies to any employer that employs four or more persons, or has one or more domestic workers. "
                "Independent contractors working in furtherance of an employer's business count toward the four-employee threshold.\n\n"
                "The requirement applies to all advertisements for jobs, promotions, or transfer opportunities. An advertisement is "
                "broadly defined as any written notice or posting distributed to potential applicants, including job boards, flyers, "
                "social media advertisements, newspaper listings, and internal company bulletin boards."
            ),
            (
                "Good-Faith Salary Range Mandate",
                "The advertised wage scale or salary range must extend from the lowest to the highest annual salary or hourly wage "
                "that the employer in good faith believes at the time of the posting it would pay for the advertised role. "
                "Open-ended ranges such as '$100,000 and up' or 'maximum $150,000' are strictly unlawful. The minimum and maximum "
                "cannot be left open or unbounded.\n\n"
                "If an employer has no flexibility and offers a fixed rate of pay (for example, exactly $30 per hour or $90,000 annually), "
                "the employer may state that exact single figure instead of a range."
            ),
            (
                "Remote and Multi-Jurisdictional Workers",
                "The law explicitly applies to any job that can or will be performed, at least in part, in New York City. "
                "This includes positions where an employee works in an office, field location, or remotely from their home located "
                "within any of the five boroughs of New York City.\n\n"
                "For fully remote positions, if the job could be performed by an employee residing in New York City, employers "
                "must comply with the salary range disclosure mandates regardless of where company headquarters are located."
            ),
            (
                "Penalties and Enforcement",
                "The New York City Commission on Human Rights (CCHR) enforces Local Law 32. For first-time violations, "
                "employers receive a 30-day cure period from receiving notice of violation to submit proof that the deficiency has "
                "been resolved, resulting in zero civil penalty. However, uncorrected or subsequent violations can result in civil "
                "penalties of up to $250,000 under the NYCHRL."
            ),
        ],
    },
    {
        "filename": "pay_transparency_colorado.pdf",
        "title": "Colorado Equal Pay for Equal Work Act (EPEW) Statutory Guidelines",
        "is_compliance": True,
        "sections": [
            (
                "Legislative Intent and Scope",
                "The Colorado Equal Pay for Equal Work Act (C.R.S. § 8-5-101 et seq.), enhanced by subsequent amendments, aims to eliminate "
                "gender-based wage disparities by requiring pay transparency in all job postings and promotional announcements. "
                "Any employer with at least one employee in Colorado must comply with these disclosure provisions for any job that "
                "could be performed in Colorado, including remote positions."
            ),
            (
                "Mandatory Compensation and Benefits Disclosures",
                "Under Part 2 of the Act, every job posting must include: "
                "1. The hourly rate or salary compensation range that the employer in good faith believes it will pay for the job. "
                "2. A general description of any bonuses, commissions, or other forms of incentive compensation. "
                "3. A general description of all employment benefits, including health care benefits, retirement benefits, paid days off, "
                "and any tax-advantaged accounts.\n\n"
                "Postings must also specify the date on which application submissions are anticipated to close, or state that applications "
                "are accepted on an ongoing rolling basis."
            ),
            (
                "Promotional Opportunities Notice",
                "Employers are obligated to notify all Colorado employees of all job opportunities, career progressions, and promotional "
                "vacancies within the organization on or before the day the employer begins considering external applicants. "
                "The notification must outline job qualifications, application deadlines, and salary parameters."
            ),
            (
                "Prohibition on Wage History Inquiries",
                "The Colorado statute strictly forbids employers from seeking, requesting, or relying upon the wage rate history of "
                "a prospective employee to determine wage rates. Employers may not discharge or discriminate against employees who inquire "
                "about, discuss, or compare compensation data with colleagues."
            ),
        ],
    },
    {
        "filename": "pay_transparency_california.pdf",
        "title": "California Pay Transparency and Wage Equality (SB 1162)",
        "is_compliance": True,
        "sections": [
            (
                "Statutory Background (California SB 1162)",
                "California Senate Bill 1162 expanded California Labor Code § 432.3 to require comprehensive pay transparency "
                "in published job listings. Employers with 15 or more employees—where at least one employee is located in California—must "
                "include the pay scale for every position in any job posting. The 15-employee threshold counts all employees nationally."
            ),
            (
                "Pay Scale Definition and Third-Party Compliance",
                "A 'pay scale' is defined as the salary or hourly wage range that the employer reasonably expects to pay for the position. "
                "Employers that engage third-party recruiting agencies, recruitment marketing vendors, or job boards to advertise openings "
                "must provide the compliant pay scale to the third party, and that third party is legally bound to display it in the advertisement."
            ),
            (
                "Record Keeping Requirements",
                "Employers must maintain job title records and wage rate history for each employee throughout the duration of employment "
                "plus an additional three years following termination. These records must be open to inspection by the California Labor "
                "Commissioner to verify whether there is a pattern of wage disparity."
            ),
            (
                "Fines and Civil Penalties",
                "Persons who claim to be aggrieved by a failure to include salary ranges may file a written complaint with the "
                "Labor Commissioner or pursue a civil action. Penalties for non-compliance range from $100 to $10,000 per violation, "
                "determined based on the totality of circumstances and history of prior infractions."
            ),
        ],
    },
    {
        "filename": "pay_transparency_washington.pdf",
        "title": "Washington State Equal Pay and Opportunities Act (EPOA)",
        "is_compliance": True,
        "sections": [
            (
                "Applicability and Mandate (RCW 49.58.050)",
                "Washington State's Equal Pay and Opportunities Act requires employers with 15 or more employees to disclose in each "
                "job posting the wage scale or salary range, alongside a general description of all benefits and other compensation. "
                "This mandate covers any position that could be performed by a Washington-based employee, including remote positions "
                "open to candidates nationwide."
            ),
            (
                "Content of the Required Disclosures",
                "1. Wage Scale / Salary Range: Must show the minimum and maximum pay rate (e.g., $65,000 - $85,000 per year, or $32.00 - $40.00 "
                "per hour). Open-ended phrases like '$60k+' are prohibited.\n"
                "2. Other Compensation: Postings must specify eligibility for bonuses, stock options, profit sharing, commission structures, "
                "or sign-on incentives.\n"
                "3. Benefits Description: Must outline medical, dental, vision, life insurance, retirement/401(k) matching, and paid leave options."
            ),
            (
                "Internal Transfers and Promotions",
                "Upon request of an existing employee who is offered an internal transfer or promotion, the employer must provide the wage "
                "scale or salary range for the new position."
            ),
            (
                "Enforcement Mechanisms",
                "The Washington Department of Labor & Industries (L&I) investigates wage transparency complaints. Aggrieved job seekers "
                "and employees may recover actual statutory damages, statutory penalties ranging from $500 to $5,000 per violation, and "
                "reasonable attorneys' fees."
            ),
        ],
    },
    {
        "filename": "job_ad_writing_best_practices.pdf",
        "title": "Job Advertisement Architecture and Copywriting Best Practices",
        "is_compliance": False,
        "sections": [
            (
                "Job Descriptions vs. Job Advertisements",
                "A foundational error in recruitment marketing is treating internal HR job descriptions as external job advertisements. "
                "An internal job description is an operational and legal document detailing governance, grade, and exhaustive task lists. "
                "An external job advertisement is a targeted marketing piece designed to attract, engage, and convert qualified candidates. "
                "Effective job ads focus on candidate impact, team mission, and realistic technical challenges rather than administrative duties."
            ),
            (
                "The Anatomical Framework of High-Converting Job Ads",
                "1. Standardized Role Title: Avoid internal company codes (e.g., 'MTS-IV') or quirky labels ('Code Ninja'). Use industry "
                "standard titles ('Senior Backend Engineer - Python/Distributed Systems') to maximize organic search discovery.\n"
                "2. The Hook (Mission & Value Proposition): 3 to 4 sentences outlining the problem the team is solving and why the role matters.\n"
                "3. Core Responsibilities (First 90-180 Days): 4 to 6 outcome-oriented bullets describing tangible deliverables.\n"
                "4. Qualifications (Must-Haves vs. Nice-to-Haves): Limit hard requirements to 4-5 genuine dealbreakers.\n"
                "5. Transparent Compensation & Benefits: Transparent base pay range, healthcare, equity, and remote work policy."
            ),
            (
                "Readability and Cognitive Load",
                "Eye-tracking research shows that candidates scan job postings in an F-shaped pattern for an average of 45 to 60 seconds "
                "before deciding whether to apply or abandon the page. Bullet lists exceeding 7 items induce cognitive fatigue. "
                "Keep sentences under 25 words, maintain clear section headers, and preserve ample whitespace."
            ),
            (
                "Call to Action and Conversion Optimization",
                "Make the application pathway frictionless. Requiring candidates to re-enter resume details manually into legacy forms "
                "creates drop-off rates exceeding 70%. Ensure the 'Apply Now' call to action is visible above the fold and at the footer."
            ),
        ],
    },
    {
        "filename": "inclusive_language_and_bias_reduction.pdf",
        "title": "Inclusive Language and Bias Reduction in Talent Sourcing",
        "is_compliance": False,
        "sections": [
            (
                "The Impact of Language Coding on Sourcing Pools",
                "Decades of linguistic research in industrial-organizational psychology reveal that vocabulary in job postings alters "
                "the demographics of the applicant pool. Inadvertently coded language deters underrepresented groups from applying, "
                "even when they possess all requisite technical skills."
            ),
            (
                "Gender-Coded Phrasing Patterns",
                "Masculine-coded adjectives and verbs (e.g., 'aggressive', 'dominant', 'ninja', 'rockstar', 'crush', 'fearless') "
                "significantly depress female application rates. Conversely, feminine-coded language (e.g., 'collaborative', 'supportive', "
                "'interpersonal', 'inclusive', 'empathetic') encourages balanced gender participation without discouraging male applicants. "
                "Best practice: Audit all copy for masculine-coded terms and replace them with objective competency descriptions."
            ),
            (
                "Age Bias and Exclusionary Traps",
                "Phrases like 'recent college graduate', 'digital native', or 'energetic youth' communicate ageist preferences and can trigger "
                "claims under the Age Discrimination in Employment Act (ADEA). Furthermore, specifying 'maximum 5 years experience' implies "
                "overqualification bias. Focus strictly on minimum technical capabilities rather than artificial career tenure caps."
            ),
            (
                "Requirements Inflation and the Confidence Gap",
                "Internal studies indicate that men frequently apply when meeting 60% of listed qualifications, whereas women and "
                "underrepresented candidates tend to apply only when meeting 100% of listed criteria. Distinguish strictly between "
                "'Essential Qualifications' and 'Preferred Skills' to prevent unintentional self-selection out of the candidate pool."
            ),
        ],
    },
    {
        "filename": "recruitment_marketing_fundamentals.pdf",
        "title": "Recruitment Marketing Fundamentals: Programmatic Buying and Unit Economics",
        "is_compliance": False,
        "sections": [
            (
                "The Shift to Data-Driven Recruitment Media",
                "Recruitment marketing has evolved from static 'post-and-pray' job board contracts to dynamic, programmatic media buying. "
                "Modern recruitment platforms optimize job ad distribution in real-time across hundreds of job sites, search engines, "
                "and social networks based on talent supply and demand algorithms."
            ),
            (
                "Core Commercial Metrics: CPC, CPA, and CPH",
                "1. Cost-Per-Click (CPC): The dollar amount paid every time a prospective candidate clicks on a sponsored job advertisement. "
                "CPC = Total Media Spend / Total Clicks.\n"
                "2. Cost-Per-Application (CPA): The cost required to generate a completed candidate application. CPA = Total Spend / Applications.\n"
                "3. Cost-Per-Hire (CPH): Total investment (advertising media + agency fees + recruiter overhead) divided by total hires made.\n\n"
                "Optimizing the application conversion funnel from Click -> Apply is essential: a high click volume with low apply conversion "
                "wastes advertising capital on non-converting traffic."
            ),
            (
                "Budget Pacing and Algorithmic Distribution",
                "Unmanaged recruitment budgets frequently suffer from premature exhaustion: 80% of a monthly job ad budget is spent in the "
                "first week, leaving critical positions unadvertised later in the hiring cycle. Programmatic pacing engines dynamically adjust "
                "bids and throttle spend when application volume goals are met, redirecting budget to hard-to-fill technical roles."
            ),
            (
                "Channel Mix Optimization",
                "Different talent personas concentrate on distinct acquisition channels. Niche engineering communities, programmatic aggregators "
                "(Indeed, ZipRecruiter, LinkedIn), and targeted search ads must be balanced dynamically based on real-time cost-per-qualified-lead."
            ),
        ],
    },
    {
        "filename": "ats_and_application_funnel_metrics.pdf",
        "title": "ATS Architecture and Recruitment Application Funnel Analytics",
        "is_compliance": False,
        "sections": [
            (
                "The Modern Recruitment Application Funnel",
                "The hiring lifecycle operates as a quantitative conversion funnel: "
                "Impressions -> Job Ad Views (Clicks) -> Application Starts -> Completed Applications -> Phone Screens -> Technical "
                "Interviews -> Onsite / Final Rounds -> Offers Extended -> Offers Accepted.\n\n"
                "Tracking conversion velocity and attrition at each stage isolates whether bottlenecks stem from poor job ad messaging, "
                "cumbersome application forms, or misaligned interview expectations."
            ),
            (
                "Benchmark Conversion Rates",
                "- View-to-Apply Conversion: Industry benchmarks average 8% to 15% for desktop, but drop to 3% to 6% for mobile devices "
                "if the application requires multi-page manual data entry.\n"
                "- Screen-to-Interview Conversion: Typically 30% to 50% for well-targeted programmatic sourcing.\n"
                "- Offer Acceptance Rate (OAR): High-performing talent organizations target OAR >= 85%. An OAR below 75% indicates "
                "compensation lag, protracted interview loops, or misaligned candidate expectations."
            ),
            (
                "ATS Data Schemas and Tracking Integrations",
                "Applicant Tracking Systems (ATS) like Greenhouse, Lever, and Workday rely on standardized candidate data models. "
                "Source tracking utilizes UTM parameters and unique referral tokens to attribute each applicant to the exact recruitment "
                "media campaign, enabling multi-touch attribution analysis."
            ),
            (
                "Drop-Off Remediation Strategies",
                "To reduce candidate abandonment, implement single-click social apply (e.g., LinkedIn / GitHub profile parsing), "
                "eliminate redundant account creation requirements prior to resume submission, and ensure maximum 3-minute completion time."
            ),
        ],
    },
    {
        "filename": "candidate_experience_guidelines.pdf",
        "title": "Candidate Experience Standards and Employer Brand Protection",
        "is_compliance": False,
        "sections": [
            (
                "The Business Impact of Candidate Experience",
                "In recruitment marketing, candidate experience is inseparable from customer brand equity. Research shows that 60% of "
                "job seekers report a negative hiring experience, and 72% share those negative experiences on public review platforms "
                "like Glassdoor or social media. Negative candidate sentiment directly inflates recruitment media CPCs as candidates become "
                "resistant to company outreach."
            ),
            (
                "Communication SLA Standards",
                "Establishing and adhering to Service Level Agreements (SLAs) for applicant communication is critical: "
                "1. Immediate Automated Confirmation: Acknowledge application receipt within 5 minutes.\n"
                "2. Status Update Within 5 Business Days: Inform candidates whether their application is advancing or declined.\n"
                "3. Post-Interview Debrief: Deliver interview outcomes within 48 to 72 hours following any interview stage."
            ),
            (
                "The Anti-Ghosting Mandate",
                "Allowing candidates who reached the interview stage to experience indefinite silence ('ghosting') creates enduring brand damage. "
                "Every interviewed candidate deserves prompt, dignified closure. Providing constructive, respectful feedback fosters "
                "long-term talent communities that can be resurfaced for future openings without recurring acquisition spend."
            ),
            (
                "Accessibility and Mobile Optimization",
                "All hiring touchpoints must comply with Web Content Accessibility Guidelines (WCAG 2.1 AA), ensuring screen reader "
                "compatibility, keyboard navigation, and high-contrast color palettes for neurodiverse and visually impaired applicants."
            ),
        ],
    },
    {
        "filename": "structured_interviewing_and_rubrics.pdf",
        "title": "Structured Interviewing Protocols and Objective Evaluation Rubrics",
        "is_compliance": False,
        "sections": [
            (
                "Unstructured vs. Structured Interviewing",
                "Industrial psychology research demonstrates that unstructured 'free-form chat' interviews have low predictive validity "
                "(r ~ 0.14 to 0.20) for on-the-job performance and are vulnerable to confirmation bias and similarity attraction. "
                "Structured interviews—where candidates are asked the same predetermined, competency-based questions evaluated against "
                "calibrated scoring rubrics—deliver significantly higher predictive validity (r ~ 0.51 to 0.65)."
            ),
            (
                "Designing Behavioral and Situational Questions",
                "Effective structured interview questions utilize the STAR methodology (Situation, Task, Action, Result) to evaluate past "
                "demonstrated competencies. For example: 'Describe a production outage in a distributed system you resolved. What monitoring "
                "signals did you trace, what mitigation steps did you execute, and what preventative architecture did you deploy?'"
            ),
            (
                "Calibrated Evaluation Rubrics",
                "Each competency must be measured on a 1-to-4 or 1-to-5 anchored rubric: "
                "1 - Unsatisfactory: Failed to identify root cause; relied on guessing. "
                "2 - Developing: Identified symptom but struggled to explain underlying system bottleneck. "
                "3 - Proficient: Systematically isolated fault domain using metrics and logs; implemented clean hotfix. "
                "4 - Exemplary: Designed architectural guardrail and automated circuit breaker preventing entire fault class."
            ),
            (
                "Mitigating Cognitive Biases",
                "Independent scoring before committee debriefs prevents groupthink and senior-interviewer dominance. Interviewers must "
                "document evidence-based observations rather than generic impressions like 'good culture fit'."
            ),
        ],
    },
]


def build_pdf(doc_def: dict, output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=12,
        textColor="#1a365d",
    )

    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
        textColor="#2b6cb0",
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        spaceAfter=10,
        textColor="#2d3748",
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontSize=8.5,
        leading=12,
        textColor="#742a2a",
        spaceAfter=14,
    )

    story = []

    # Title
    story.append(Paragraph(doc_def["title"], title_style))
    story.append(Spacer(1, 6))

    # Compliance disclaimer if applicable
    if doc_def.get("is_compliance"):
        story.append(Paragraph(DISCLAIMER, disclaimer_style))
        story.append(Spacer(1, 8))

    # Sections
    sections = doc_def["sections"]
    for i, (sec_title, sec_text) in enumerate(sections):
        story.append(Paragraph(f"{i + 1}. {sec_title}", h2_style))
        paragraphs = sec_text.split("\n\n")
        for p in paragraphs:
            story.append(Paragraph(p.strip(), body_style))
        if i == 1:
            # Force a page break after 2nd section to ensure multi-page document structure
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 8))

    doc.build(story)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    corpus_dir = repo_root / "data" / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating recruitment corpus in {corpus_dir}...")
    for doc_def in DOCUMENTS:
        target_path = corpus_dir / doc_def["filename"]
        build_pdf(doc_def, target_path)
        print(f"Generated: {doc_def['filename']}")

    # Clean up legacy machine learning pdf if present
    legacy_pdf = corpus_dir / "Logistic_Regression (1).pdf"
    if legacy_pdf.exists():
        legacy_pdf.unlink()
        print("Removed legacy Logistic_Regression (1).pdf")

    print(f"Successfully generated {len(DOCUMENTS)} recruitment PDFs.")


if __name__ == "__main__":
    main()
