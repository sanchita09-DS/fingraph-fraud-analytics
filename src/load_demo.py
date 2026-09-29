"""Generate synthetic transactions and load them into Neo4j."""

import os
import random
from uuid import uuid4

from dotenv import load_dotenv
from neo4j import GraphDatabase
from simulator import make_transaction

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")


def build_transactions():
    transactions = []

    # Five ordinary transfers between different accounts.
    for number in range(1, 6):
        sender = random.randint(5, 20)
        receiver = random.randint(5, 20)

        while receiver == sender:
            receiver = random.randint(5, 20)

        transactions.append(make_transaction(number, sender, receiver))

    # A predictable three-step trail for detection practice.
    trail = [(1, 2), (2, 3), (3, 4)]

    for number, (sender, receiver) in enumerate(trail, start=6):
        transaction = make_transaction(number, sender, receiver)
        transaction["amount"] = 1200 - (number - 6) * 20
        transactions.append(transaction)

    # Give every run a unique batch ID.
    batch_id = uuid4().hex[:8]

    for transaction in transactions:
        transaction["transaction_id"] = (
            f"{batch_id}-{transaction['transaction_id']}"
        )

    return transactions


def main():
    if not URI or not USER or not PASSWORD:
        raise RuntimeError(
            "Neo4j settings are missing from the root .env file."
        )

    query = """
    MERGE (sender:Account {account_id: $sender_account})
    MERGE (receiver:Account {account_id: $receiver_account})
    MERGE (sender)-[transfer:TRANSFERRED_TO {
        transaction_id: $transaction_id
    }]->(receiver)
    SET transfer.amount = $amount,
        transfer.currency = $currency,
        transfer.timestamp = datetime($timestamp)
    """

    transactions = build_transactions()

    with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
        driver.verify_connectivity()

        with driver.session(database="neo4j") as session:
            for transaction in transactions:
                session.run(query, **transaction).consume()

    print(f"Loaded {len(transactions)} synthetic transfers into Neo4j.")


if __name__ == "__main__":
    main()