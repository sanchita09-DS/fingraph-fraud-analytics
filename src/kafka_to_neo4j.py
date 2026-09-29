"""Read Flink-processed Kafka events and store them in Neo4j."""

import json
import os

from dotenv import load_dotenv
from kafka import KafkaConsumer
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

QUERY = """
MERGE (sender:Account {account_id: $sender_account})
MERGE (receiver:Account {account_id: $receiver_account})
MERGE (sender)-[transfer:TRANSFERRED_TO {
    transaction_id: $transaction_id
}]->(receiver)
SET transfer.amount = $amount,
    transfer.currency = $currency,
    transfer.timestamp = datetime($timestamp),
    transfer.risk_score = $risk_score,
    transfer.flink_processed = $flink_processed
"""


def main():
    if not URI or not USER or not PASSWORD:
        raise RuntimeError(
            "Neo4j settings are missing from the root .env file."
        )

    consumer = KafkaConsumer(
        "transactions-processed",
        bootstrap_servers="localhost:9092",
        group_id="fingraph-neo4j-writer",
        auto_offset_reset="earliest",
        consumer_timeout_ms=10000,
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
    )

    count = 0

    try:
        with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
            driver.verify_connectivity()

            with driver.session(database="neo4j") as session:
                for message in consumer:
                    event = message.value
                    session.run(QUERY, **event).consume()
                    count += 1
                    print(
                        f"Saved {event['transaction_id']} "
                        f"with risk score {event['risk_score']}"
                    )
    finally:
        consumer.close()

    print(f"Saved {count} Flink-processed transfers to Neo4j.")


if __name__ == "__main__":
    main()