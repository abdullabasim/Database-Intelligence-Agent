# Database Intelligence Agent

The Database Intelligence Agent is a professional-grade, multi-tenant platform built with FastAPI and LangGraph. It is designed to enable secure, natural language interactions with any PostgreSQL database. By leveraging a Semantic Metadata Layer (MDL) and a sophisticated reasoning pipeline, the system provides an intelligent abstraction bridge between complex user questions and secure SQL execution.

---

## The Reasoning Engine (LangGraph)

The platform utilizes a state-controlled LangGraph reasoning machine that orchestrates a multi-stage execution pipeline to ensure high accuracy and security.

### 6-Stage Execution Pipeline
1.  MDL Lookup: Retrieves semantic metadata for the target database. If no MDL exists, the agent initiates an automated discovery phase to understand the schema.
2.  Intent Analysis: Deconstructs the natural language question to identify target entities, filters, and analytical metrics.
3.  SQL Generation: Transpiles intent into optimized PostgreSQL queries. The agent can switch between Exploration and Final modes.
4.  SQL Validation and Sanitization: A critical security gate that inspects generated SQL for destructive commands and ensures it adheres to read-only constraints.
5.  Execution and Self-Correction: Runs the query against the target database.
6.  Answer Synthesis: Transforms raw query results into a polished, human-readable response.

### Internal Schema Discovery (Sub-Agent Logic)
When the agent is unsure about specific data values needed for JOINs or WHERE conditions (e.g., the exact spelling of a category or a product name), it generates an EXPLORE query. This internal sub-step allows the agent to search for valid constants before attempting a final analytical query, significantly reducing errors in filtering and relationship mapping.

### Self-Correction and Resiliency
The agent features an automated retry loop. If a generated SQL query fails during execution, the system captures the specific database error and feeds the traceback back into the LangGraph loop. The agent then performs a reasoning update to fix the syntax or logic errors, attempting to self-heal up to 3 times before reporting a problem.

---

## Security and Governance Architecture

Security is baked into the core of the platform using standardized FastAPI layers and cryptographic services.

### Credential Protection
- Encryption at Rest: All external database credentials are stored using AES-256 Fernet Encryption. Encryption keys are managed through isolated system environment variables.
- Tenant Isolation: Database connections are strictly partitioned by user_id, ensuring users can only interact with their own registered data sources.

### Semantic Metadata Layer (MDL)
The MDL serves as the system's primary security control and semantic bridge:
- Metadata Masking: The agent never receives direct access to your primary schema definitions. It only interacts with the metadata stored in the MDL, protecting internal database structures.
- Explicit Blocking: Administrators can select specific tables to be excluded from the MDL. If a table is not in the MDL, the agent is logically unaware of its existence.
- Enriched Context: Technical column names are enriched with business descriptions, allowing the LLM to understand what the data represents rather than just how it is stored.

---

## Operational Workflow and Automation

The platform is optimized for modern DevOps workflows and rapid deployment.

### Automated Deployment
The platform is fully containerized. Upon running docker compose up, the system completes its own initialization automatically:
1.  Migration sync: Automatically applies the latest Alembic migrations to the internal metadata store.
2.  System Seeding: Initializes the environment with a default administrator and core configuration.
3.  Health Verification: Monitors the readiness of the PostgreSQL metadata store before starting the API.

---

## Quick Start

### 1. Launch the Stack
Run the following command to start the Database, API, and Frontend. The system handles its own database migrations and initial data seeding during this process.
```bash
docker compose up -d --build
```

### 2. Access Points
- Intelligence Dashboard: http://localhost:3000
- Interactive API Docs: http://localhost:8000/docs
- Default Credentials: admin@example.com / admin123

---

## Future Roadmap

- NoSQL and Multi-DB Support: Support for MongoDB, MySQL, and Microsoft SQL Server.
- Vector Database Integration: Implementing RAG-based analysis of technical documentation using Pinecone or Chroma.
- Cross-Database Reasoning: Enabling the agent to join and analyze data across multiple disconnected database connections.

