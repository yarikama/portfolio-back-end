<!--
Henry's resume as plain text, for the "ask about my work" chat. Converted by
hand from the general modules in the resume_latex repo (content/resume/,
commit a406414, 2026-09-18). The real job titles come from the GenAI
variant; the backend detail from the SWE variant is merged in under them.
Left out on purpose: phone number and street address. Projects are left
out too: every resume project is already a project on the site.
Update this when the resume changes.
-->

# Resume: Henry Hsu

Website: www.yarikama.com · LinkedIn: linkedin.com/in/yarikama · GitHub: github.com/yarikama · Based in Houston, TX. To get in touch, use the contact form on this site.

## Summary

Software Engineering Intern at Google and former Generative AI Team Lead, shipping production GenAI platforms and agentic developer infrastructure. Grew a B2B platform's client base by 120% and its user base from 3K to 20K through agentic AI systems, advanced RAG and backend infrastructure, including enterprise rollouts at CTBC Bank, MSI and HPE; the product won two major industry awards. Now pursuing an M.C.S. at Rice University, graduating December 2026.

## Work experience

### Software Engineering Intern, Google (Taipei, Taiwan), Jun. 2026 – Aug. 2026

- Integration test infrastructure: built 3 test infrastructures from zero (Java, Python), onboarding 400+ integration test suites across 200+ smart home device types, with 90%+ unit test coverage for the infrastructure itself.
- Agentic failure triage: developed an LLM agent that triages scheduled integration test runs and posts root-cause summaries directly on issue tickets, replacing manual log inspection and cutting failure narrow-down time by 20+ minutes per issue.
- Local device reproduction: extended the agent to reproduce device failures locally against virtual devices instead of waiting on cloud runs, cutting manual reproduction time by 85%. Shipped and adopted by the team.

### Generative AI Team Lead, MaiAgent Co., Ltd. (Taipei, Taiwan), Dec. 2024 – Aug. 2025

MaiAgent is an award-winning B2B generative AI startup.

- Building AI agents: upgraded chatbots into AI agents with memory systems, tool APIs and an MCP client, resulting in 120% partner growth (CTBC Bank, MSI, HPE, iGroup) and user growth from 3K to 20K, while cutting LLM token usage by 67%+.
- Technical roadmap and leadership: defined the GenAI product roadmap for a 10-person startup; led feasibility evaluation and end-to-end delivery of production features including agentic RAG, artifact generation, a tagging and permission system, and information retrieval.
- API optimization: optimized 140+ REST APIs through SQL query refactoring, connection pooling (Elasticsearch, Cohere, OpenAI) and Django caching; cut the response time of 13 high-traffic APIs by 27.7% overall and eliminated N+1 queries.
- Testing and CI/CD: introduced pytest unit and end-to-end tests and a GitHub Actions CI pipeline, reaching 67% coverage from zero; production hotfixes dropped 90% at first and stayed 50% lower long term. Managed database migrations in the CD pipeline.
- Open source: contributed 14 merged pull requests to LlamaIndex (15K+ stars), fixing bugs and adding features in the AWS Bedrock, Claude, Elasticsearch, Cohere, OpenAI, MCP client and agent workflow integrations.

### Generative AI Intern, MaiAgent Co., Ltd. (Taipei, Taiwan), Sep. 2024 – Dec. 2024

- Pipeline scaling: refactored the document indexing pipeline onto an async framework (asyncio, Celery) with relational and vector database synchronization, parsing 3.5x faster and scaling from 3M to 20M+ text chunks while doubling indexing performance.
- Reranker integration: integrated Cohere and open-source BGE rerankers as a customer-selectable retrieval feature, improving RAG precision on large documents by 30% (Precision@5) and 7% (Precision@10).
- Real-time communication: built a WebSocket notification system with Redis pub/sub for file parsing status, and an event-driven architecture for agent state transitions that pushes live updates to the frontend.

## Education

- **Rice University** (Houston, TX), top 20 U.S. university. M.C.S., Computer Science, GPA 4.00/4.00. Aug. 2025 – Dec. 2026 (expected).
- **National Yang Ming Chiao Tung University (NYCU)** (Hsinchu, Taiwan), top 3 university in Taiwan. B.S., Industrial Engineering and Management, GPA 4.07/4.30, two-time Dean's List; minor in Computer Science (domain GPA 4.13/4.30). Sep. 2020 – Jun. 2024.

## Awards

- Presidential Hackathon winner (2024, top 5 nationally): an urban noise agent built on a structured-output LLM pipeline with tool calling.
- 23rd Golden Peak Award (2025): Outstanding Commercial Product, for the MaiAgent AI platform.
- AI Workshop Outstanding Award (top 3 of 50 teams), NYCU Computer Science: a multi-agent RAG tutoring system.
- Atona Case Competition (ATCC): project lead of a team in the top 20 nationally, out of 2,000+ registered teams.

## Skills

- Languages: Python, Java, C/C++, TypeScript, JavaScript.
- Generative AI: LlamaIndex, LangChain, LangGraph, MCP; RAG, rerankers, AI agents.
- Backend: Django, FastAPI, Express.js; REST, WebSocket, Redis pub/sub; asyncio, Celery.
- Frontend: React, HTML, CSS.
- Databases: PostgreSQL, MongoDB, Elasticsearch, Neo4j, Milvus.
- Data science and ML: NumPy, pandas, scikit-learn, PyTorch, JAX.
- Testing and DevOps: pytest, JUnit, Vitest; GitHub Actions, Docker, git, Nginx, shell scripting.
- AWS: Bedrock, EMR, EC2, S3, RDS, ElastiCache, SageMaker.

## Leadership

- President, Student Association of Industrial Engineering and Management, NYCU (Jun. 2022 – Jun. 2023): managed four teams of 37 people and ran 20+ events in a year; refurbished the student shared space on a tight budget.
- Student representative, NYCU College of Management Affairs Committee (Sep. 2023 – Jul. 2024): took part in 10+ amendment drafts, including the committee selection procedure and the school's development white paper.
