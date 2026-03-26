# Nexus Engine Architecture Overview

This document outlines the architectural decisions and technical implementation of the Nexus Engine, a graph-powered LLM intelligence layer for SAP "Order-to-Cash" (O2C) datasets.

## 1. Data Ingestion Architecture
- **Inference Engine**: The system uses a dynamic `IngestionEngine` that scans 19+ SAP-structured JSONL directories. 
- **Dynamic Schema**: Instead of hardcoded DDL, the engine infers column names and types from the first record of every table, enabling the system to survive upstream SAP schema changes.
- **SQLite Choice**: SQLite was chosen as the target for its zero-latency local execution, which is critical for providing near-instant responses to the LLM's SQL generation.

## 2. Graph Modelling & Ontology
The graph is designed for **Cross-Functional Traceability**.
- **Ontology**: 
    - `Business Partner` --(placed)--> `Sales Order`
    - `Sales Order` --(shipped_as)--> `Delivery`
    - `Sales Order` --(invoiced_as)--> `Invoice`
- **Visualization Modes**:
    - **Constellation**: High-clarity view focusing on primary relationships.
    - **Nebula**: Dense, interconnected view of the entire enterprise web.
- **Node Glow System**: Nodes use a custom canvas rendering script in the frontend that calculates a dynamic "glow halo" based on entity type and selection state, ensuring a premium "Dark Aurora" aesthetic.

## 3. LLM Intelligence Layer
- **Prompt Engineering**: The `llm_service.py` uses a "Ground Truth" injected prompt. This includes:
    - **ISO Mapping**: Mapping human terms ("India") to storage terms ("IN").
    - **Status Mapping**: Mapping human terms ("Delivered") to SAP status codes ("C").
    - **Automatic Deduplication**: The system is trained to use `SELECT DISTINCT` when joining across item-level tables (Deliveries/Invoices) to prevent row inflation.
- **Guardrail Strategy**: Uses a dual-layer regex and term-matching system to ensure query safety while remaining permissive to natural language variations.

## 4. Frontend "Nexus UI"
- **Bespoke Layout**: A custom flex-layout with a fixed-width Command Center (sidebar) and a liquid-width Graph Panel.
- **Performance**: Large datasets (16k+ rows) are handled via frontend truncation (first 100 rows) and a scrollable viewport, balancing exploration speed with browser stability.
