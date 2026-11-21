state_labels = {
    "borrower_number": "Borrower",
    "third_party_number": "Third Party",
    "not_borrower_number": "Not Borrower",
    "invalid_number": "Invalid Number",
    "switched_off": "Switched Off"
}

action_labels = {
    "CALL_BEST_CONTACT": "Call Best Contact",
    "TRY_BEST_CONTACT": "Try Best Contact",
    "RETRY_OR_SWITCH_TIME": "Retry / Switch Time",
    "DEPRIORITIZE_CONTACT": "Deprioritize",
    "REVIEW_CONTACT_SET": "Review Contact Set",
    "SKIP_TRACE_NOW": "Skip Trace Now",
    "SKIP_TRACE_LOW_PRIORITY": "Low Priority Trace",
    "DO_NOT_SKIP_TRACE": "Do Not Trace"
}

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


import streamlit as st
import pandas as pd
st.set_page_config(
    page_title="Contact Intelligence Engine",
    page_icon="📞",
    layout="wide"
)

st.title("Contact Intelligence & Skip-Trace Prioritisation")

st.caption(
    "RPC prediction • Contact health • Compliance suppression • "
    "Economic skip-trace prioritisation"
)

@st.cache_data
def load_data():

    decisions = pd.read_csv(
        DATA_DIR / "final_decision_engine.csv"
    )

    contacts = pd.read_csv(
        DATA_DIR / "contact_decision_table.csv"
    )

    skips = pd.read_csv(
        DATA_DIR / "skip_trace_prioritization.csv"
    )

    return decisions, contacts, skips


decisions, contacts, skips = load_data()
total_accounts = len(decisions)

call_now = (
    decisions["final_action"]
    == "CALL_BEST_CONTACT"
).sum()

skip_now = (
    decisions["final_action"]
    == "SKIP_TRACE_NOW"
).sum()

review = (
    decisions["final_action"]
    == "REVIEW_CONTACT_SET"
).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Accounts",
    f"{total_accounts:,}"
)

c2.metric(
    "Call Best Contact",
    f"{call_now:,}"
)

c3.metric(
    "Skip Trace Now",
    f"{skip_now:,}"
)

c4.metric(
    "Compliance Review",
    f"{review:,}"
)

st.subheader("Portfolio Decision Distribution")

action_labels = {
    "CALL_BEST_CONTACT": "Call Best Contact",
    "TRY_BEST_CONTACT": "Try Best Contact",
    "RETRY_OR_SWITCH_TIME": "Retry / Switch Time",
    "DEPRIORITIZE_CONTACT": "Deprioritize",
    "REVIEW_CONTACT_SET": "Review Contact Set",
    "SKIP_TRACE_NOW": "Skip Trace Now",
    "SKIP_TRACE_LOW_PRIORITY": "Low Priority Trace",
    "DO_NOT_SKIP_TRACE": "Do Not Trace"
}

action_chart = (
    decisions["final_action"]
    .value_counts()
    .rename_axis("action")
    .reset_index(name="accounts")
)

action_chart["action"] = (
    action_chart["action"]
    .map(action_labels)
    .fillna(action_chart["action"])
)

st.bar_chart(
    action_chart,
    x="action",
    y="accounts",
    horizontal=True
)

st.subheader("Borrower Decision Explorer")

account_list = (
    decisions["account_id"]
    .astype(str)
    .tolist()
)

selected_account = st.selectbox(
    "Select Account",
    account_list
)

account_row = decisions[
    decisions["account_id"].astype(str)
    == selected_account
].iloc[0]

st.markdown(
    f"## Recommended Action: `{account_row['final_action']}`"
)

st.write(
    account_row["decision_reason"]
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Recoverable Exposure",
    f"₹{account_row['recoverable_exposure']:,.0f}"
)

c2.metric(
    "Best RPC Probability",
    f"{account_row['best_rpc_probability']:.1%}"
    if pd.notna(account_row["best_rpc_probability"])
    else "N/A"
)

c3.metric(
    "Best Contact Score",
    f"{account_row['best_contact_score']:.3f}"
    if pd.notna(account_row["best_contact_score"])
    else "N/A"
)

c4.metric(
    "Portfolio Priority",
    f"#{int(account_row['overall_priority_rank'])}"
)


st.subheader("Known Contact Points")

account_contacts = contacts[
    contacts["account_id"].astype(str)
    == selected_account
].copy()

contact_columns = [
    "phone_id",
    "source",
    "relation_recorded",
    "operational_state",
    "rpc_probability",
    "safe_probability",
    "contact_priority_score",
    "final_phone_rank",
    "recommended_action"
]

available_contact_columns = [
    col
    for col in contact_columns
    if col in account_contacts.columns
]

st.dataframe(
    account_contacts[
        available_contact_columns
    ],
    use_container_width=True,
    hide_index=True
)

if account_row["skip_trace_candidate"] == 1:

    st.subheader("Skip-Trace Economics")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Trace Success Probability",
        f"{account_row['p_trace_success']:.1%}"
        if pd.notna(account_row["p_trace_success"])
        else "N/A"
    )

    c2.metric(
        "Expected Gross Recovery",
        f"₹{account_row['expected_gross_recovery']:,.0f}"
        if pd.notna(account_row["expected_gross_recovery"])
        else "N/A"
    )

    c3.metric(
        "Trace Cost",
        f"₹{account_row['cost_inr']:,.0f}"
        if pd.notna(account_row["cost_inr"])
        else "N/A"
    )

    c4.metric(
        "Net Expected Value",
        f"₹{account_row['net_expected_value']:,.0f}"
        if pd.notna(account_row["net_expected_value"])
        else "N/A"
    )


    st.subheader("Priority Queue")

priority_columns = [
    "overall_priority_rank",
    "account_id",
    "best_phone_id",
    "best_phone_state",
    "best_rpc_probability",
    "recoverable_exposure",
    "final_action",
    "account_priority_score"
]

available_priority_columns = [
    col
    for col in priority_columns
    if col in decisions.columns
]

st.dataframe(
    decisions[
        available_priority_columns
    ].head(100),
    use_container_width=True,
    hide_index=True
)

pretty_action = action_labels.get(
    account_row["final_action"],
    account_row["final_action"]
)

st.markdown(
    f"## Recommended Action: `{pretty_action}`"
)

account_contacts["operational_state"] = (
    account_contacts["operational_state"]
    .map(state_labels)
    .fillna(account_contacts["operational_state"])
)

account_contacts["recommended_action"] = (
    account_contacts["recommended_action"]
    .str.replace("_", " ")
    .str.title()
)

st.dataframe(
    account_contacts[
        available_contact_columns
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "rpc_probability": st.column_config.ProgressColumn(
            "RPC Probability",
            min_value=0,
            max_value=1,
            format="%.1%%"
        ),

        "safe_probability": st.column_config.ProgressColumn(
            "Safe Contact Probability",
            min_value=0,
            max_value=1,
            format="%.1%%"
        ),

        "contact_priority_score": st.column_config.NumberColumn(
            "Contact Score",
            format="%.3f"
        ),

        "final_phone_rank": st.column_config.NumberColumn(
            "Rank",
            format="%d"
        )
    }
)
st.subheader("Portfolio Priority Queue")

c1, c2 = st.columns(2)

with c1:
    selected_actions = st.multiselect(
        "Filter by Action",
        options=decisions["final_action"].unique(),
        default=list(decisions["final_action"].unique())
    )

with c2:
    top_n = st.slider(
        "Number of Accounts",
        min_value=10,
        max_value=200,
        value=50,
        step=10
    )

filtered_queue = decisions[
    decisions["final_action"].isin(selected_actions)
].head(top_n)


