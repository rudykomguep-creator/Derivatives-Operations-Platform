# ⬡ DerivOps — Derivatives Operations Platform

A full-stack derivatives trade support system built with Streamlit and SQLite.
Covers the complete operations lifecycle: trade capture → reconciliation → affirmation → settlement → accounting → lifecycle management, with an AI assistant powered by Claude.

## Modules

| Module | Description |
|--------|-------------|
| 📊 Dashboard | KPIs, trade volume, break summary |
| 📥 Trade Capture | Manual entry, CSV/Excel import, trade repository |
| 🔄 Reconciliation | Trade, position, and cash recon with break dashboard |
| ✅ Affirmation | Counterparty matching engine + exception queue |
| 💰 Settlement | Schedule, cash tracker, failed settlement monitor |
| 📒 Accounting | Journal generator, ledger, Dr=Cr validation |
| 📅 Lifecycle | Option/future/swap lifecycle events, corporate actions |
| 🤖 AI Assistant | Claude-powered break analysis, procedure search, auto-tickets |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key (for AI Assistant module)
export ANTHROPIC_API_KEY=your_key_here

# 3. Run the app
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push this folder to a GitHub repository
2. Go to https://share.streamlit.io
3. Connect your repo, set `app.py` as entry point
4. Add `ANTHROPIC_API_KEY` in Secrets

## Tech stack

- **Frontend**: Streamlit
- **Database**: SQLite (auto-initialized with demo data)
- **AI**: Anthropic Claude (claude-sonnet-4-20250514)
- **Data**: Pandas, openpyxl
