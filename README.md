# FinGraph — Real-Time Fraud Analytics

FinGraph is an educational demonstration of a streaming transaction analytics pipeline. It processes synthetic transfers, assigns risk scores, stores the resulting graph in Neo4j, and displays account relationships in a Streamlit dashboard.

> **Disclaimer:** This project uses synthetic data and heuristic risk scores. It is for learning and demonstration only—not for real financial decisions or production fraud detection.

## Features

- Publishes synthetic transactions to Apache Kafka.
- Scores transactions in an Apache Flink streaming job.
- Stores transfers and account relationships in Neo4j.
- Uses Neo4j Graph Data Science for graph analysis, including PageRank and community detection.
- Displays transactions, risk scores, and the account network in a Streamlit dashboard.
- Supports optional Slack notifications through an incoming webhook.

## Architecture

```text
Synthetic transactions
        │
        ▼
      Kafka
        │
        ▼
 Apache Flink ── risk-scored transactions
        │
        ▼
      Kafka
        │
        ▼
 Neo4j graph database
        │
        ├── Graph analysis
        └── Streamlit dashboard
                 │
                 └── Optional Slack alerts

Technology
- Python
- Apache Kafka
- Apache Flink
- Neo4j Community Edition
- Neo4j Graph Data Science
- Streamlit
- Docker Compose
- Maven
Requirements
Install these tools before running the project:
- Docker Desktop
- Python 3
- Java 17
- Apache Maven
- Git

Project structure
.
├── app.py                    # Streamlit dashboard
├── compose.yaml              # Neo4j, Kafka, and Flink services
├── requirements.txt          # Python dependencies
├── queries/
│   └── queries/              # Cypher graph queries
├── src/
│   ├── kafka_to_neo4j.py     # Reads processed events into Neo4j
│   ├── load_demo.py          # Loads sample transfers
│   ├── publish_transactions.py
│   ├── read_transactions.py
│   └── simulator.py
└── flink/
    ├── pom.xml               # Maven build configuration
    └── src/main/java/        # Flink transaction scoring job
