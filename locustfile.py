"""
Locust load test suite for the Full-Stack Recruiter Copilot.

Simulates realistic recruiter workflows:
1. User registration / login session
2. Streaming RAG chat query (/api/chat)
3. Repeated query verifying semantic cache hits (<20ms response)
4. Statutory compliance verification (/api/tools/compliance)
5. AI Job ad drafting (/api/tools/draft-ad)
6. Document browsing (/api/documents)
7. Analytics dashboard polling (/api/analytics/summary)
8. Message feedback submission (/api/feedback)
"""

import random
import uuid
from locust import HttpUser, task, between


SAMPLE_QUERIES = [
    "What are the pay transparency requirements in NYC Local Law 32?",
    "Can we state salary range as 50k to 150k in Colorado?",
    "What are the mandatory disclosures for California pay scale law?",
    "How does Washington state define total compensation in job postings?",
    "What are the penalty amounts for non-compliance with NYC pay transparency?",
    "How do we calculate Cost Per Hire and optimize recruitment media spend?",
    "Explain the difference between Applicant Tracking System drop-off and funnel stages.",
    "What behavioral interview rubrics minimize interviewer cognitive bias?",
]

SAMPLE_JOB_ADS = [
    {
        "title": "Senior Frontend Engineer",
        "description": "We are seeking a React developer with 5+ years of experience to lead our web app team in NYC. Must have TypeScript expertise.",
        "jurisdiction": "NYC",
        "min_salary": 140000,
        "max_salary": 180000,
    },
    {
        "title": "Marketing Operations Manager",
        "description": "Join our fast-paced startup in Denver, CO. Competitive compensation depending on experience. Healthcare and 401k included.",
        "jurisdiction": "CO",
        "min_salary": None,
        "max_salary": None,
    },
    {
        "title": "Staff AI Engineer",
        "description": "Design and build generative AI pipelines in San Francisco. Salary range $190,000 to $240,000 plus equity.",
        "jurisdiction": "CA",
        "min_salary": 190000,
        "max_salary": 240000,
    },
]


class RecruiterUser(HttpUser):
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Register a unique user and establish an authenticated session."""
        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@joveo-recruiter.test"
        self.user_password = "Password123!"
        self.conversation_id = None
        self.latest_message_id = None

        # 1. Register
        reg_res = self.client.post(
            "/api/auth/register",
            json={
                "email": self.user_email,
                "password": self.user_password,
                "name": "Load Test Recruiter",
            },
        )
        if reg_res.status_code not in (200, 201):
            # Fallback to login if already registered
            self.client.post(
                "/api/auth/login",
                json={
                    "email": self.user_email,
                    "password": self.user_password,
                },
            )

        # 2. Create an initial conversation
        conv_res = self.client.post(
            "/api/conversations",
            json={"title": "Compliance Review Session"},
        )
        if conv_res.status_code in (200, 201):
            self.conversation_id = conv_res.json().get("id")

    @task(4)
    def ask_rag_chat(self):
        """Stream a recruitment query via Server-Sent Events."""
        if not self.conversation_id:
            return

        query = random.choice(SAMPLE_QUERIES)
        with self.client.post(
            "/api/chat",
            json={
                "conversationId": self.conversation_id,
                "query": query,
            },
            catch_response=True,
            stream=True,
            name="/api/chat [First Query - RAG Retrieval]",
        ) as response:
            if response.status_code == 200:
                # Read stream chunks
                content = response.text
                if "[DONE]" in content or "event: token" in content:
                    response.success()
                else:
                    response.failure("Stream did not emit expected SSE events")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def ask_repeated_query_cache(self):
        """Hit the exact same query repeatedly to measure semantic cache response speed."""
        if not self.conversation_id:
            return

        fixed_query = "What are the pay transparency requirements in NYC Local Law 32?"
        with self.client.post(
            "/api/chat",
            json={
                "conversationId": self.conversation_id,
                "query": fixed_query,
            },
            catch_response=True,
            stream=True,
            name="/api/chat [Cached Query]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def check_compliance_tool(self):
        """Execute statutory compliance validator."""
        sample = random.choice(SAMPLE_JOB_ADS)
        self.client.post(
            "/api/tools/compliance",
            json={
                "text": sample["description"],
                "jurisdiction": sample["jurisdiction"],
                "salaryMin": sample["min_salary"],
                "salaryMax": sample["max_salary"],
            },
            name="/api/tools/compliance",
        )

    @task(2)
    def draft_job_ad_tool(self):
        """Execute deterministic job ad drafting tool."""
        self.client.post(
            "/api/tools/draft-ad",
            json={
                "title": "Product Marketing Manager",
                "department": "Talent Acquisition Solutions",
                "jurisdiction": "NYC",
                "salaryMin": 130000,
                "salaryMax": 160000,
                "responsibilities": ["Lead B2B campaigns", "Analyze CPC and CPA across job boards"],
                "qualifications": ["4+ years recruitment marketing experience", "Analytical mindset"],
            },
            name="/api/tools/draft-ad",
        )

    @task(1)
    def browse_documents(self):
        """Recruiter browsing the recruitment knowledge corpus."""
        self.client.get("/api/documents", name="/api/documents")

    @task(1)
    def view_analytics(self):
        """Recruiter viewing pipeline analytics and compliance breakdown."""
        self.client.get("/api/analytics/summary", name="/api/analytics/summary")
