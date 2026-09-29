"""Publish synthetic transactions to Kafka."""

import json

from kafka import KafkaProducer
from load_demo import build_transactions


def main():
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda event: json.dumps(event).encode("utf-8"),
    )

    try:
        transactions = build_transactions()

        for transaction in transactions:
            producer.send("transactions", transaction)

        producer.flush()
        print(f"Sent {len(transactions)} transactions to Kafka.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()