# Recruiter Copilot: 2-Minute Demonstration Script

This walkthrough script guides a technical reviewer or interviewer through the primary recruiter workflows, demonstrating full-stack cohesion, real-time token streaming, semantic cache acceleration, source citation transparency, and statutory compliance enforcement.

---

## Pre-requisites
Ensure the platform is running (`docker compose up` or local dev servers on port 3000):
- Open your browser to: `http://localhost:3000`
- Default Demo Account:
  - **Email**: `recruiter@example.com`
  - **Password**: `Password123!`

---

## Step 1: Authentication & Workspace Overview (0:00 - 0:25)

1. Navigate to `/login`.
2. Enter the demo credentials (`recruiter@example.com` / `Password123!`) and click **Sign in to Workspace**.
3. You are redirected to `/chat`.
4. Notice the clean, high-density recruiter workspace:
   - Left sidebar with previous conversations and quick action shortcuts.
   - Main conversational stage with statutory quick-prompt cards.
   - Quick action tools: **Check Compliance** and **Draft Job Ad**.

---

## Step 2: RAG Retrieval & Streaming Verification (0:25 - 0:50)

1. In the chat input box at the bottom, enter the following prompt (or click the quick card):
   > *"What are the mandatory salary disclosure rules in NYC Local Law 32?"*
2. Click the send button (or press `Enter`).
3. **Observe the interactions**:
   - The user message appears instantly.
   - The assistant stream begins immediately via Server-Sent Events (SSE).
   - A **Stop Generation** button is active while streaming tokens arrive.
   - The response includes the statutory minimum and maximum salary range requirement, employer size threshold (4+ employees), and prohibition on open-ended ranges like "$50k and up".
   - Notice the citation chip at the end: `[nyc_pay_transparency_law.pdf, Page 1]`.

---

## Step 3: Citation Verification Drawer (0:50 - 1:10)

1. Click directly on the citation chip: `[nyc_pay_transparency_law.pdf, Page 1]`.
2. **Observe**:
   - The **Citation Sources** panel smoothly opens on the right side of the screen.
   - The panel displays the document title, exact page number, relevance score, and the excerpted legal text retrieved directly from the hybrid vector/keyword index.
   - Close the panel by clicking the `X` button.

---

## Step 4: Semantic Cache Acceleration Demonstration (1:10 - 1:25)

1. Submit a natural rephrasing of the same inquiry:
   > *"What does NYC Local Law 32 require employers to include in job postings?"*
2. **Observe**:
   - Notice the green badge: **"Served from semantic cache"** with a sub-10ms response time indicator.
   - The answer is served instantly without triggering upstream LLM token costs or dense/sparse index re-execution.
   - Behind the scenes: Qdrant identified the cosine similarity ($\ge 0.95$) against the cached question embedding, verified that `corpus_version` is current, and returned the verified cached answer.

---

## Step 5: Statutory Compliance Checker Tool (1:25 - 1:40)

1. In the top toolbar, click **Check Compliance**.
2. The modal dialog opens.
3. Select **Jurisdiction**: `New York City (NYC)`.
4. In the Job Description text box, paste the following non-compliant text:
   > *"We are looking for an experienced software developer to join our team. Competitive salary based on previous salary history. Applicants must have no more than 7 years of experience."*
5. Click **Verify Compliance**.
6. **Observe the deterministic rule auditor**:
   - **Violation 1**: Missing mandatory base salary or hourly wage range under NYC Local Law 32.
   - **Violation 2**: Prohibited inquiry regarding prior or current salary history.
   - **Warning 3**: Maximum experience cap ("no more than 7 years") flagged as potential age bias.

---

## Step 6: AI-Assisted Job Ad Drafting (1:40 - 1:50)

1. Click **Draft Job Ad** in the top toolbar.
2. Enter:
   - **Role Title**: `Senior Full-Stack Engineer`
   - **Department / Level**: `Mid-Senior`
   - **Jurisdiction**: `Colorado (CO)`
   - **Salary Range**: `$140,000 - $180,000`
   - **Must-Have Skills**: `TypeScript, React, Node.js, PostgreSQL`
3. Click **Generate Compliant Ad**.
4. **Observe**:
   - A structured, inclusive job description is generated.
   - Explicit salary boundaries and Colorado-required benefit disclosures are automatically included.
   - Copy the generated ad to clipboard with a single click.

---

## Step 7: Recruiter Analytics Dashboard (1:50 - 2:00)

1. Click **Analytics** in the left sidebar (navigating to `/analytics`).
2. **Observe the aggregated intelligence**:
   - Total questions answered and messages exchanged.
   - **Satisfaction Rate**: Calculated live from thumbs up/down feedback stored in PostgreSQL.
   - **Semantic Cache Efficiency**: Percentage of queries served from cache vs. cold RAG executions.
   - **Compliance Audit Breakdown**: Distribution of audits by jurisdiction (NYC, CO, CA, WA).
   - Recharts visual graphs rendering query volume and latency trends.

---

## Wrap-up
This demonstration showcases an end-to-end recruitment technology copilot built with modern software engineering principles: robust TypeScript types, relational database modeling, atomic distributed caching, vector embeddings, and real-time streaming interfaces.
