# Database Intelligence Agent

## The Problem

Most organizations sit on top of databases that only a handful of engineers can actually use. If a product manager wants to know which customers churned last month, or a business analyst needs to understand why revenue dropped in a specific region, they have to file a ticket and wait. The data exists. The answers exist. But access is gated behind SQL knowledge, schema familiarity, and engineering bandwidth.

Even when you give someone direct database access, new problems emerge. They may query the wrong tables, expose sensitive records, or write inefficient joins that lock up production systems. The gap between the person asking the question and the person who can answer it is a real, daily cost for most teams.

This project was built to close that gap.

---

## What It Does

The Database Intelligence Agent lets you connect any PostgreSQL database and interact with it using plain language. You ask a question, and the system figures out the rest.

For example:

- "What were the top five products by revenue last quarter?"
- "Show me all customers who placed more than three orders but haven't purchased in 60 days."
- "How do customer ratings compare across different product categories?"

The agent reads your question, understands the structure of your database, constructs a safe and accurate SQL query, runs it, and returns a human-readable answer. No SQL. No schema knowledge required.

---

## How It Actually Works

A single LLM call is not enough to do this reliably. Real databases have ambiguous column names, missing relationships, and values that do not match what users expect to find. To handle this, the system runs a multi-agent pipeline powered by LangGraph, where each stage is a specialized node responsible for one specific task.

### The Pipeline

When a question comes in, it moves through the following stages:

First, the system loads the Semantic Metadata Layer for the connected database. This is a pre-generated map of your schema that includes business descriptions for every table and column, not just the raw technical definitions. The agent works from this map, not directly from your database schema.

Second, the agent analyzes the intent behind your question. It identifies which tables are relevant, what filters apply, and what the user is actually looking for.

Third, SQL generation begins. This is where it gets interesting. The agent does not always generate a final query on the first try. If it needs to verify a value before using it in a filter or JOIN condition, it generates an internal exploration query first. For example, if you ask about a product called "Mountain Bike", the agent will check what the actual stored value is before writing the final WHERE clause. This prevents the most common class of errors in text-to-SQL systems, where generated queries reference values that do not exist in the database.

Fourth, every generated query passes through a validation layer before execution. The system checks that the query is read-only, does not reference any blocked or sensitive tables, and does not contain dangerous keywords. If any check fails, the pipeline stops and the user receives a clear explanation.

Fifth, the query executes against your database. If execution fails due to a syntax error or unexpected schema condition, the agent captures the error, feeds it back into the reasoning loop, and attempts to fix the query. This retry process runs up to three times before the system reports a problem.

Finally, the raw results are passed to a formatting agent that synthesizes the data into a clear, conversational answer.

### Why Async Matters

Database schema inspection for large systems is slow. A database with hundreds of tables, foreign key relationships, and custom column semantics can take time to analyze. The Semantic Metadata Layer generation runs as a background task, meaning the user triggers it and the system processes it without blocking anything else. The API remains fully responsive while the agent works in the background, and the new metadata becomes available automatically once the process completes.

---

## The Semantic Metadata Layer (MDL)

MDL stands for Modeling Definition Language. In the context of this project, it refers to a structured, machine-readable description of your database that the agent reads and reasons from instead of querying your schema directly.

### Why raw schema access is not enough

When you hand a language model a raw database schema, you are giving it a list of technical artifacts, table names, column names, data types, and foreign keys. What you are not giving it is meaning.

A column named `txn_dt` could be a transaction date, a transfer date, or something entirely different. A table named `ord_ref` might hold order references, but whether that means customer orders, internal work orders, or purchase orders depends on your business. A column called `status` exists in almost every table in every database, and it almost never uses the same set of values.

Language models handle ambiguity by guessing, and guessing at scale across complex schemas produces wrong queries. The joins are wrong, the filters miss, and the aggregations use the wrong base tables. Users get answers that look plausible but are factually incorrect.

This is the core problem the MDL was built to solve.

### What the MDL contains

The MDL is generated by the agent itself by inspecting your database schema and using an LLM to enrich each element with semantic context. The output is a structured document stored per database connection and versioned over time. It contains the following:

Table descriptions explain what each table actually represents in business terms, not just its technical name. A table called `ord_hdr` becomes "Order Header: the primary record for each customer order, including status, placement date, and total value."

Column descriptions map every column to its business meaning. A column called `cust_ref_id` becomes "Customer Reference ID: the unique identifier linking this record to the customer account."

Metric definitions capture how key business numbers should be calculated. If revenue means the sum of line item amounts minus credits, that logic lives in the MDL so the agent applies it consistently across every query that involves revenue.

Date conventions describe how time is stored and how common time expressions should be translated. If your system stores dates in UTC and your users ask about "last month," the MDL tells the agent exactly how to construct that filter.

Relationship hints describe how tables relate to each other beyond what foreign keys express. Sometimes two tables are joined through a bridge table that is not obvious from the schema structure alone. The MDL makes those paths explicit.

Blocked tables are listed explicitly. Any table an administrator marks as sensitive is excluded from the MDL entirely, which means the agent never learns it exists and cannot reference it in any query.

### Why this approach works well with agents

An agent that works from a fixed, curated description of the data is far more predictable than one that inspects the schema fresh on every request. The MDL gives the agent a stable ground truth to reason from. Every question, regardless of how it is phrased, gets answered from the same semantic foundation.

It also means the agent can be held accountable. When an answer is wrong, you can inspect the MDL to see whether the problem was in how a column was described, and fix it once rather than hoping the model guesses better next time.

The MDL is also versioned. Every time you regenerate it, a new version is stored alongside the previous ones. This means you can track how the agent's understanding of your database changes as your schema evolves, and roll back to a previous version if something regresses.

### How MDL generation works asynchronously

For large databases with hundreds of tables and thousands of columns, generating the MDL is a substantial task. It involves inspecting the schema, sampling data to understand value distributions, and making multiple LLM calls to produce rich descriptions.

Rather than blocking the API while this runs, the system offloads MDL generation to a background task. The user triggers a refresh and immediately gets a response confirming the job has started. The agent continues to answer questions using the existing MDL while the new one is being built in the background. Once generation completes, the new version is automatically activated and the agent begins using it for all subsequent queries.

This means even very large schemas do not create a poor user experience. The refresh happens silently, and the system upgrades itself without any downtime.

---

## Security

All external database credentials are encrypted at rest using AES-256 Fernet encryption before being stored. Each user's connections are completely isolated from other users. The query pipeline enforces read-only access at multiple layers, and every generated query is validated before it reaches your database. A user cannot reach another user's data, and the agent cannot write to or modify any database it is connected to.

---

## Technology Stack

- FastAPI (async Python backend, SSE streaming, OpenAPI docs)
- LangGraph (multi-agent reasoning pipeline)
- Pydantic (request/response validation and structured LLM output parsing)
- Next.js (frontend dashboard and chat interface)
- PostgreSQL (internal metadata store and target database)
- SQLAlchemy + Alembic (ORM and versioned migrations)
- Docker and Docker Compose (fully containerized deployment)
- JWT (stateless authentication and tenant isolation)
- Fernet encryption (credential storage at rest)

---

## Sample Data and Testing

The project ships with a seeding script that runs automatically on every container start. It is written to be idempotent, meaning it checks before inserting and never creates duplicates, so it is safe to run against a database in any state.

On first run, it creates a default administrator account that gives you immediate access to the dashboard and API without any manual setup:

- Email: admin@example.com
- Password: admin123

This is intentionally kept simple so that anyone cloning the project can be up and running in under a minute. For testing the agent itself, connect any PostgreSQL database you have access to through the dashboard, trigger an MDL refresh, and start asking questions.

The seeding system is designed to be extended. If you want to pre-populate the system with test database connections, sample MDL schemas, or additional user accounts for team testing, the seed script is the right place to add that logic. It uses the same async SQLAlchemy session pattern as the rest of the application.

---

## Getting Started

The full stack runs with a single command. The system handles database migrations and initial data setup automatically on first run.

```bash
docker compose up -d --build
```

Once the containers are running:

- Dashboard: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Default login: admin@example.com / admin123

---

## What's Next

The current release supports PostgreSQL. Planned future work includes:

- Support for MySQL, SQL Server, and MongoDB
- Background task for MDL generation, so that large schemas with hundreds of tables do not block the API while the agent inspects and enriches the schema. The idea is to trigger the refresh and let it run silently while users continue working with the existing MDL
- A progress status endpoint so users can track how far along an MDL generation job is
- Vector database integration to allow the MDL to incorporate unstructured documentation such as internal wikis or API specs, enabling the agent to reason about data it cannot directly query
