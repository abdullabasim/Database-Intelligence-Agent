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

Every tool in this stack was chosen for a specific reason. This is not a generic boilerplate setup. Each technology solves a real problem that came up during the design of this system.

### FastAPI

The backend is built on FastAPI, an asynchronous Python web framework. The choice matters here because the agent pipeline involves multiple I/O-heavy steps: loading metadata from the database, calling the LLM, executing SQL on an external connection, and streaming the result back to the client. A synchronous framework would block on each of these steps. FastAPI uses Python's async/await model throughout, which means the server can handle many concurrent requests without waiting for any single one to finish.

FastAPI also provides automatic OpenAPI documentation generation. Every route, request schema, and response model is documented and testable at `/docs` without any extra configuration. This made development and debugging significantly faster.

### LangGraph

LangGraph is the framework that orchestrates the multi-agent pipeline. The core idea behind LangGraph is that an AI reasoning process should be modeled as a directed graph, where each node is a specific task and the edges between them represent conditional logic.

In this system, each stage of the pipeline is a separate node: loading the MDL, understanding the question, generating SQL, validating it, executing it, and formatting the answer. The graph decides which node runs next based on the output of the previous one. If the SQL fails, the graph loops back to generation. If validation catches a dangerous query, the graph skips execution entirely and routes to the format node with an error message.

This structure makes the agent behavior explicit and testable. You can look at the graph definition and understand exactly what happens in every possible scenario. It also makes it easy to add new nodes or change routing logic without touching the rest of the pipeline.

### Pydantic

Pydantic is used in two distinct places in this system. The first is standard FastAPI usage: every API request and response is validated against a Pydantic model, which means malformed data never reaches the business logic layer.

The second use is more specific to the agent: LLM responses are structured using Pydantic schemas. When the MDL builder asks the LLM to describe a table or column, the response is parsed into a typed Pydantic model rather than treated as raw text. This prevents incomplete or malformed LLM outputs from being stored in the MDL. If the model returns something that does not match the expected structure, the system catches it, logs it, and either retries or skips that element. This is what makes the MDL generation reliable rather than fragile.

### Next.js

The frontend is a Next.js application. Next.js was chosen because of its built-in support for server-side rendering and API integration. The dashboard, database management views, and chat interface are all handled within a single cohesive application rather than a collection of disconnected pages.

The chat interface uses Server-Sent Events to stream responses from the backend as they arrive, rather than waiting for the entire answer to complete before showing anything. This gives users immediate feedback and makes long-running queries feel interactive rather than frozen.

### PostgreSQL

PostgreSQL serves two roles in this system. The first is as the internal metadata store: it holds user accounts, database connection records, encrypted credentials, MDL schemas, and conversation history. The second role is as the target database type that users connect to for analysis.

These are two completely separate database connections. The internal store is managed by the application. The user's connected database is accessed read-only through a dynamically constructed connection using decrypted credentials at query time.

Alembic manages all migrations for the internal store. Every schema change is versioned and applied automatically on startup, so there is no manual migration step required when deploying a new version.

### Docker and Docker Compose

The entire stack, PostgreSQL, FastAPI, and Next.js, runs inside Docker containers orchestrated by Docker Compose. The entrypoint script for the backend container runs migrations and seeds the initial data before starting the server, which means a clean deployment is always a single command with no manual steps.

The containers share an internal network, so the frontend calls the backend by container name rather than host IP, and the backend connects to PostgreSQL the same way. This behavior is identical across local development and any server deployment.

### Alembic

Alembic is the database migration tool used to manage every schema change to the internal PostgreSQL store. Rather than modifying the database directly, every change is written as a versioned migration file. When the application starts, the entrypoint script runs `alembic upgrade head`, which applies any pending migrations in order before the server accepts requests.

This means the database schema is always in sync with the code, regardless of how many times or from which state the system is deployed. Rolling forward is automatic. Rolling back is a single command. Every migration is stored alongside the application code in version control, so you can always trace exactly when and why the schema changed.

The migrations cover the full internal schema: user accounts, hashed passwords, database connection records, encrypted credential fields, MDL schema versions, and chat conversation history.

### Database Seeding

The seeding system runs immediately after migrations and is responsible for initializing the application into a usable state. On first run, it checks for the existence of a default administrator account and creates one if it does not exist. On subsequent runs, it skips silently.

The seeder is designed to be idempotent, meaning it is safe to run multiple times without creating duplicate data or causing errors. This matters because the entrypoint script runs both migrations and seeding on every container start. Whether the database is brand new or has been running for months, the result is always the same: the required baseline data is present.

The seeding logic is written as a standard async Python module using SQLAlchemy, which means it follows the same session and transaction patterns as the rest of the application. It can be extended to seed any kind of initial reference data, not just user accounts.

### JWT Authentication

All API routes are protected using JSON Web Tokens. When a user logs in, the backend issues a signed JWT containing the user's ID and expiry timestamp. The frontend stores this token and attaches it to every subsequent request via the Authorization header.

The backend verifies the token on each request before allowing access to any protected resource. The token is signed using a secret key configured through environment variables, and it expires after a configurable duration. Expired or tampered tokens are rejected immediately.

This approach keeps the backend stateless: the server does not need to maintain sessions or look up any state to verify a request. It reads the token, verifies the signature, extracts the user identity, and proceeds. This scales naturally because any number of server instances can validate the same token without coordinating with each other.

The user identity extracted from the token is then used to enforce tenant isolation. Every database query, every MDL lookup, and every connection record is scoped to the `user_id` from the token, so there is no way for one user's request to accidentally reach another user's data.

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

The current system supports PostgreSQL. The next phase of development will extend support to other relational and non-relational databases, including MySQL, SQL Server, and MongoDB. We are also exploring the use of vector databases to allow the MDL to incorporate unstructured documentation, so the agent can reason about data it cannot directly query.
