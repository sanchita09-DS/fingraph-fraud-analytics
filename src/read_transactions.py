"""Read synthetic transactions from Kafka."""

import json

from kafka import KafkaConsumer


def main():
    consumer = KafkaConsumer(
        "transactions",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        consumer_timeout_ms=10000,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    count = 0

    try:
        for message in consumer:
            event = message.value
            print(
                f"{event['transaction_id']}: "
                f"{event['sender_account']} -> "
                f"{event['receiver_account']} "
                f"(${event['amount']})"
            )
            count += 1
    finally:
        consumer.close()

    print(f"Read {count} transactions from Kafka.")


if __name__ == "__main__":
    main()