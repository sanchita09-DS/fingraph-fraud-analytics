"""Generate synthetic transfers, including a predictable suspicious money trail."""

import json
import random
from datetime import datetime, timezone


def make_transaction(transaction_id: int, sender: int, receiver: int) -> dict:
    return {
        "transaction_id": f"TX-{transaction_id:04d}",
        "sender_account": f"ACC-{sender:03d}",
        "receiver_account": f"ACC-{receiver:03d}",
        "amount": round(random.uniform(10, 5000), 2),
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    # Normal transfers between different randomly selected accounts.
    for number in range(1, 6):
        sender = random.randint(5, 20)
        receiver = random.randint(5, 20)
        while receiver == sender:
            receiver = random.randint(5, 20)
        print(json.dumps(make_transaction(number, sender, receiver)))

    # A fixed three-step trail, included every time for detection practice.
    suspicious_trail = [(1, 2), (2, 3), (3, 4)]
    for number, (sender, receiver) in enumerate(suspicious_trail, start=6):
        print(json.dumps(make_transaction(number, sender, receiver)))


if __name__ == "__main__":
    main()