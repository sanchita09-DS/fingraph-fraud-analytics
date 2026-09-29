import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pyvis.network import Network
import json
from urllib.request import Request, urlopen

load_dotenv()

st.set_page_config(page_title="FinGraph Fraud Analytics", layout="wide")
st.title("FinGraph — Real-Time Fraud Analytics")
st.caption(
    "Synthetic transaction data for an internship project. "
    "PageRank measures network influence; it is not a fraud probability."
)

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

SLACK_WEBHOOK_URL = os.getenv("https://hooks.slack.com/services/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")
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.7"))

def send_slack_alert(row):
    message = (
        "*FinGraph high-risk transfer*\n"
        f"Transaction: {row['transaction_id']}\n"
        f"From: {row['sender']} to {row['receiver']}\n"
        f"Amount: ${float(row.get('amount') or 0):,.2f}\n"
        f"Risk score: {float(row.get('risk_score') or 0):.2f}"
    )
    body = json.dumps({"text": message}).encode("utf-8")
    request = Request(
        SLACK_WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"Slack returned status {response.status}")

QUERY = """
MATCH (sender:Account)-[t:TRANSFERRED_TO]->(receiver:Account)
RETURN sender.account_id AS sender,
       receiver.account_id AS receiver,
       t.transaction_id AS transaction_id,
       t.amount AS amount,
       coalesce(t.risk_score, 0.1) AS risk_score,
       sender.pagerank AS sender_pagerank,
       sender.communityId AS sender_community,
       receiver.pagerank AS receiver_pagerank,
       receiver.communityId AS receiver_community
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

accounts = {}

for row in transfers:
    risk = float(row.get("risk_score") or 0)

    for side in ("sender", "receiver"):
        account_id = row[side]
        account = accounts.setdefault(
            account_id,
            {"pagerank": 0.0, "community": None, "high_risk": False},
        )
        account["pagerank"] = float(row.get(f"{side}_pagerank") or 0)
        account["community"] = row.get(f"{side}_community")
        account["high_risk"] = account["high_risk"] or risk >= 0.7

high_risk_count = sum(float(row.get("risk_score") or 0) >= 0.7 for row in transfers)

if "sent_slack_alerts" not in st.session_state:
    st.session_state["sent_slack_alerts"] = set()

sent_ids = st.session_state["sent_slack_alerts"]
alerts_sent = 0

if SLACK_WEBHOOK_URL:
    for row in transfers:
        transaction_id = row["transaction_id"]
        risk = float(row.get("risk_score") or 0)

        if risk >= ALERT_THRESHOLD and transaction_id not in sent_ids:
            try:
                send_slack_alert(row)
                sent_ids.add(transaction_id)
                alerts_sent += 1
            except Exception as error:
                st.warning(f"Slack alert could not be sent: {error}")

if alerts_sent:
    st.success(f"Sent {alerts_sent} high-risk alert(s) to Slack.")

community_ids = sorted({
    account["community"]
    for account in accounts.values()
    if account["community"] is not None
})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transfers shown", len(transfers))
col2.metric("Accounts shown", len(accounts))
col3.metric("High-risk transfers", high_risk_count)
col4.metric("Communities shown", len(community_ids))

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

community_palette = [
    "#38bdf8",
    "#a78bfa",
    "#34d399",
    "#fbbf24",
    "#fb7185",
    "#2dd4bf",
    "#c084fc",
    "#a3e635",
]
community_colors = {
    community: community_palette[index % len(community_palette)]
    for index, community in enumerate(community_ids)
}

for account_id, details in accounts.items():
    community = details["community"]
    color = "#ef4444" if details["high_risk"] else community_colors.get(
        community, "#38bdf8"
    )
    size = 14 + min(details["pagerank"] * 8, 18)

    network.add_node(
        account_id,
        label=account_id,
        color=color,
        size=size,
        font={"color": "white", "size": 16},
        title=(
            f"Account: {account_id}<br>"
            f"PageRank: {details['pagerank']:.4f}<br>"
            f"Louvain community: {community}<br>"
            f"Connected to high-risk transfer: {details['high_risk']}"
        ),
    )

for row in transfers:
    amount = float(row.get("amount") or 0)
    risk = float(row.get("risk_score") or 0)

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