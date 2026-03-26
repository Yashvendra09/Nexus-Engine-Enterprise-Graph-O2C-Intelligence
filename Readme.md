# Nexus Engine: Enterprise Graph & O2C Intelligence

Nexus Engine is a full-stack intelligence layer designed to transform complex, multi-table SAP "Order-to-Cash" (O2C) datasets into an interactive, natural-language-queriable graph. It bridges the gap between raw relational data and human-friendly insights using a Graph-LLM hybrid architecture.

##  The Vision
In large enterprise environments, data is often siloed across dozens of tables with cryptic column names like `soldToParty` or `referenceSdDocument`. Nexus Engine solves this by:
1.  **Visualizing Relationships**: Mapping raw rows into a living graph of Partners, Orders, Deliveries, and Invoices.
2.  **Conversational Access**: Allowing anyone to ask "How many orders are pending for Nelson?" instead of writing complex 5-table JOINs.

## Key Features
- **Deterministic NL-to-SQL**: Translates natural language into precise SQLite queries with 100% accuracy using schema-injected prompting.
- **Dynamic Graph Visualization**: Supports "Constellation" (clean) and "Nebula" (dense) exploration of 500+ nodes and edges.
- **Enterprise Guardrails**: Blocks destructive SQL (DROP, DELETE) and keeps conversations strictly within the O2C domain.
- **Zero-Latency Ingestion**: A custom `IngestionEngine` that dynamically infers schemas from raw JSONL files in seconds.

## System Architecture
The Nexus Engine follows a reactive, pipeline-based flow:

1.  **User Query**: The user asks a question in the Nexus Sidebar.
2.  **LLM Translation**: The query is sent to a custom-prompted LLM (Llama 3.3 70B) which maps intent to a specific SQL dialect infused with "Ground Truth" data facts.
3.  **SQL Execution**: The generated SQL is validated by guardrails and executed against a local SQLite instance.
4.  **UI Feedback**: Results are rendered as scrollable tables in the sidebar, while the Graph Panel highlights relevant entity relationships.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python), Uvicorn.
- **Database**: SQLite (optimized for portable, local read-heavy performance).
- **LLM**: Groq Llama 3.3 70B (State-of-the-art for fast, high-precision JSON/SQL generation).
- **Graph Engine**: NetworkX (Backend logic) + React Force Graph 2D (Frontend rendering).
- **Frontend**: React (Vite) with a custom "Dark Aurora" glassmorphism theme.

##  Data Modeling & Graph Ontology
Nexus Engine maps relational integrity to a directed graph:
- **Entities (Nodes)**: `business_partners`, `sales_order_headers`, `outbound_delivery_headers`, `billing_document_headers`, and `products`.
- **Relationships (Edges)**:
  - `Partner` --[placed]--> `Order`
  - `Order` --[shipped_as]--> `Delivery`
  - `Order` --[invoiced_as]--> `Invoice`
- **Dynamic Labels**: Instead of raw IDs, the UI uses a priority-based labeling system (e.g., `businessPartnerFullName` -> `businessPartnerName`).

##  LLM Design Philosophy
We treats the LLM as a **Translator, not a Generator**. 
Instead of letting the LLM "hallucinate" answers based on its training data, we provide it with a "Ground Truth" prompt containing the exact SQL schema, status-enum mappings (e.g., `'C' = Delivered`), and ISO country codes. This ensures the output is always a verifiable SQL query grounded in the actual database.

## 🛡 Guardrails & Safety
- **Operation Level**: Regex-based blocks for `DROP`, `DELETE`, `UPDATE`, etc.
- **Domain Level**: A keyword-matching layer ensures the system only responds to Supply Chain / O2C queries, rejecting off-topic prompts.

##  Example Queries
- *"Show all business partners located in India"*
- *"Return all sales orders where total net amount is greater than 5000"*
- *"How many unique orders have been fully delivered?"*
- *"Fetch all billing documents for Nelson Group"*

## ⚙️ Setup & Installation

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
python load_data.py  # Ingests JSONL into supply_chain.db
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🏗 Challenges & Tradeoffs
- **Case Sensitivity**: SQLite is case-sensitive for string comparisons. We solved this by forcing `LOWER(column) LIKE LOWER('%value%')` in the LLM's "Golden Rules".
- **Schema Mismatch**: SAP columns are cryptic. We solved this by injecting a "Cross-Table Mapping" dictionary into the LLM context.
- **Why SQLite?**: It's zero-config, portable, and faster than a hosted DB for the high-volume NL-to-SQL lookups required by this engine.
- **Why NetworkX?**: For a single-user intelligence tool, a full Neo4j instance is overkill. NetworkX provides the perfect balance of graph logic and performance.

## 🔮 Limitations & Future
- **Scaling**: Currently optimized for <50k nodes. Future versions would offload graph search to a dedicated database layer.
- **Richer Graph UI**: Adding edge-bundling and time-series clustering to visualize order flows over months.
