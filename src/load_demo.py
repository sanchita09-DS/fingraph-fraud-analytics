"""Load a synthetic money trail into Neo4j."""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

TRANSACTIONS = [
    {
        "transaction_id": "TX-DEMO-001",
        "sender": "ACC-001",
        "receiver": "ACC-002",
        "amount": 1200.00,
    },
    {
        "transaction_id": "TX-DEMO-002",
        "sender": "ACC-002",
        "receiver": "ACC-003",
        "amount": 1180.00,
    },
    {
        "transaction_id": "TX-DEMO-003",
        "sender": "ACC-003",
        "receiver": "ACC-004",
        "amount": 1160.00,
    },
]


def main() -> None:
    if not URI or not USER or not PASSWORD:
        raise RuntimeError("Neo4j settings are missing from the root .env file.")

    query = """
    MERGE (sender:Account {account_id: $sender})
    MERGE (receiver:Account {account_id: $receiver})
    MERGE (sender)-[transfer:TRANSFERRED_TO {
        transaction_id: $transaction_id
    }]->(receiver)
    SET transfer.amount = $amount,
        transfer.currency = "USD",
        transfer.timestamp = datetime($timestamp)
    """

    with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
        driver.verify_connectivity()
        with driver.session(database="neo4j") as session:
            for transaction in TRANSACTIONS:
                transaction["timestamp"] = datetime.now(
                    timezone.utc
                ).isoformat()
                session.run(query, **transaction).consume()

    print(f"Loaded {len(TRANSACTIONS)} synthetic transfers into Neo4j.")


if __name__ == "__main__":
    main()