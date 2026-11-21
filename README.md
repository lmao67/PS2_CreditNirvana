# Credit Nirvana: Contact Intelligence & Skip-Trace Prioritisation

A decision engine for a debt-collection portfolio. For each overdue account it answers three questions:

1. **Which phone number should we call first?** The engine predicts the probability of a Right Party Contact (RPC) for every known number.
2. **Is that number healthy and safe to use?** It classifies each number's operational state (borrower, third party, not borrower, invalid, switched off) and suppresses risky contacts.
3. **Is it worth paying for a skip-trace?** When no usable contact exists, it weighs the expected recovery against the trace cost.

The results are combined into one recommended action per account and shown in a Streamlit dashboard.

## What it produces

For the 2,400 accounts in the portfolio, `data/final_decision_engine.csv` gives one action per account:

| Action | Accounts | Share |
|---|---:|---:|
| Call Best Contact | 1,052 | 43.83% |
| Skip Trace Now | 428 | 17.83% |
| Try Best Contact | 416 | 17.33% |
| Retry / Switch Time | 163 | 6.79% |
| Deprioritize Contact | 127 | 5.29% |
| Review Contact Set (compliance) | 98 | 4.08% |
| Skip Trace Low Priority | 58 | 2.42% |
| Do Not Skip Trace | 58 | 2.42% |

## Models

| Model | Purpose | Result on held-out data |
|---|---|---|
| RPC model (CatBoost, chosen over a logistic regression baseline) | Probability that a call attempt reaches the right party | ROC-AUC 0.697, PR-AUC 0.273, Brier 0.123 |
| Contact-state model (CatBoost) | Classifies each phone number's state | Accuracy 0.746, macro F1 0.753 |
| Skip-trace model (CatBoost) | Probability that a trace finds a new contact | ROC-AUC 0.793, PR-AUC 0.535 (about 19% of traces succeed) |

Saved models are in `models/`. The contact-state evaluation set is small (63 verified numbers), so treat those scores as indicative.

## Project structure

```
PS2_CreditNirvana/
├── app/
│   └── app.py                  # Streamlit dashboard
├── data/                       # Raw tables and engine outputs (CSV)
│   ├── accounts.csv, lenders.csv, agents.csv, payments.csv
│   ├── phone_contacts.csv, addresses.csv, verified_phone_states.csv
│   ├── dial_attempts.csv, dial_attempts_with_target.csv, field_visits.csv
│   ├── skip_trace.csv, splits.csv
│   ├── rpc_feature_table.csv   # Model features, one row per dial attempt
│   ├── phone_rpc_ranking.csv, first_call_recommendation.csv
│   ├── contact_decision_table.csv, account_contact_summary.csv
│   ├── skip_trace_prioritization.csv
│   └── final_decision_engine.csv, decision_summary.csv
├── models/
│   ├── catboost_rpc_model.cbm
│   ├── logistic_rpc_model.pkl
│   ├── contact_state_model.cbm
│   └── skip_trace_model.cbm
└── notebooks/
    ├── 01_data_understanding.ipynb
    ├── 02_feature_engineering.ipynb      # Features and RPC, contact-state and skip-trace models
    └── notebooks/04_contact_state.ipynb
```

## How the decision engine works

1. **Features.** For every dial attempt, the notebooks build history features: previous attempts, RPC rate, answer, no-answer, rejected and invalid-network rates, days since the last attempt or RPC, time of day, and account attributes (DPD, EMI, outstanding, bureau band, prior promises to pay, and so on).
2. **RPC probability.** The model scores every phone number on an account.
3. **Contact state and safety.** A second model predicts the state of each number. Verified statuses override predictions where hard evidence exists. This gives a safe-contact probability.
4. **Contact ranking.** Numbers are ranked per account by a contact priority score that combines RPC and safe probability. Each number gets a recommended action.
5. **Skip-trace economics.** For accounts with no usable contact, the engine estimates trace success probability, expected gross recovery, trace cost, net expected value and ROI, and ranks the candidates.
6. **Final action.** Contact and skip-trace outputs merge into one `final_action` per account, with a `decision_reason`, a `compliance_flag`, and an overall priority rank based on recoverable exposure.

## Setup

Requires Python 3.11 or later.

```bash
git clone https://github.com/<your-username>/PS2_CreditNirvana.git
cd PS2_CreditNirvana

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install streamlit pandas numpy catboost scikit-learn joblib matplotlib jupyter
```

## Run the dashboard

```bash
streamlit run app/app.py
```

The dashboard shows:

- Portfolio KPIs and the distribution of recommended actions
- An account explorer with the recommended action, its reason, recoverable exposure and the ranked contact points
- Skip-trace economics (success probability, expected recovery, cost, net value) for trace candidates
- A filterable priority queue of accounts

## Re-running the analysis

Open the notebooks in order (`01_data_understanding`, then `02_feature_engineering`, then `04_contact_state`) from the `notebooks/` folder with Jupyter. They read from `data/` and write the model files and decision tables back to `models/` and `data/`.

## Notes

- Phone numbers in `phone_contacts.csv` are masked.
- Amounts are in Indian rupees (INR).
