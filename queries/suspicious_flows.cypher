MATCH path = (start:Account)-[:TRANSFERRED_TO*3]->(end:Account)
WITH path, relationships(path) AS transfers, nodes(path) AS accounts
WHERE all(
  i IN range(0, size(transfers) - 2)
  WHERE transfers[i].amount >= transfers[i + 1].amount
    AND transfers[i].amount <= transfers[i + 1].amount * 1.10
)
RETURN path,
       [account IN accounts | account.account_id] AS trail,
       [transfer IN transfers | transfer.amount] AS amounts