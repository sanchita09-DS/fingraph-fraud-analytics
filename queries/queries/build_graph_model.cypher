UNWIND range(1, 20) AS n
WITH n,
     "ACC-" + right("000" + toString(n), 3) AS accountId,
     "P-" + right("000" + toString(n), 3) AS personId,
     "BANK-0" + toString((n % 3) + 1) AS bankId
MERGE (person:Person {person_id: personId})
SET person.name = "Synthetic Person " + toString(n)
MERGE (account:Account {account_id: accountId})
MERGE (bank:Bank {bank_id: bankId})
SET bank.name = bankId
MERGE (person)-[:OWNS]->(account)
MERGE (account)-[:HELD_AT]->(bank)
RETURN count(DISTINCT account) AS accounts_connected