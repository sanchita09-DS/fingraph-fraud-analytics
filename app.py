import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pyvis.network import Network

load_dotenv()

st.set_page_config(page_title="FinGraph Fraud Analytics", layout="wide")
st.title("FinGraph — Real-Time Fraud Analytics")
st.caption("Synthetic transaction data for an internship project. Not for real financial decisions.")

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

QUERY = """
MATCH (sender:Account)-[t:TRANSFERRED_TO]->(receiver:Account)
RETURN sender.account_id AS sender,
       receiver.account_id AS receiver,
       t.transaction_id AS transaction_id,
       t.amount AS amount,
       coalesce(t.risk_score, 0.1) AS risk_score
ORDER BY risk_score DESC
LIMIT 200
"""


@st.cache_data(ttl=5)
def load_transfers():
    if not PASSWORD:
        raise RuntimeError("NEO4J_PASSWORD is missing. Check the root .env file.")

    with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
        driver.verify_connectivity()
        with driver.session(database="neo4j") as session:
            result = session.run(QUERY)
            return [record.data() for record in result]


try:
    transfers = load_transfers()
except Exception as error:
    st.error(f"Could not load data from Neo4j: {error}")
    st.stop()

if not transfers:
    st.warning("No transfers found yet. Publish transactions and run the Neo4j consumer first.")
    st.stop()

high_risk_count = sum(row["risk_score"] >= 0.7 for row in transfers)
account_count = len({
    account
    for row in transfers
    for account in (row["sender"], row["receiver"])
})

col1, col2, col3 = st.columns(3)
col1.metric("Transfers shown", len(transfers))
col2.metric("Accounts shown", account_count)
col3.metric("High-risk transfers", high_risk_count)

st.subheader("Transaction network")

network = Network(
    height="580px",
    width="100%",
    directed=True,
    bgcolor="#111827",
    font_color="white",
    cdn_resources="in_line",
)
network.barnes_hut()

accounts = set()
for row in transfers:
    accounts.add(row["sender"])
    accounts.add(row["receiver"])

for account in accounts:
    network.add_node(
        account,
        label=account,
        color="#ef4444" if any(
            row["risk_score"] >= 0.7
            and account in (row["sender"], row["receiver"])
            for row in transfers
        ) else "#38bdf8",
        title=f"Account: {account}",
    )

for row in transfers:
    amount = row["amount"] or 0
    risk = row["risk_score"] or 0
    network.add_edge(
        row["sender"],
        row["receiver"],
        label=f"${amount:,.0f}",
        title=(
            f"Transaction: {row['transaction_id']}<br>"
            f"Amount: ${amount:,.2f}<br>"
            f"Risk score: {risk:.2f}"
        ),
        color="#ef4444" if risk >= 0.7 else "#94a3b8",
        arrows="to",
    )

html_path = Path("data") / "fraud_network.html"
html_path.parent.mkdir(exist_ok=True)
html = network.generate_html()
html_path.write_text(html, encoding="utf-8")

components.html(
    html_path.read_text(encoding="utf-8"),
    height=600,
    scrolling=True,
)

st.subheader("Transfers")
st.dataframe(transfers, use_container_width=True)