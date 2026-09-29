"""Generate synthetic transactions for the FinGraph project."""

import json
import random
from datetime import datetime, timezone


def make_transaction(transaction_id: int) -> dict:
    """Create one synthetic transfer between two accounts."""
    sender = random.randint(1, 20)
    receiver = random.randint(1, 20)

    while receiver == sender:
        receiver = random.randint(1, 20)

    return {
        "transaction_id": f"TX-{transaction_id:04d}",
        "sender_account": f"ACC-{sender:03d}",
        "receiver_account": f"ACC-{receiver:03d}",
        "amount": round(random.uniform(10, 5000), 2),
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    """Print five sample transactions as JSON."""
    for number in range(1, 6):
        print(json.dumps(make_transaction(number)))


if __name__ == "__main__":
    main()