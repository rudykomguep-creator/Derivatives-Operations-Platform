import streamlit as st
import pandas as pd
from utils.db import get_conn

def render():
    st.title("💰 Settlement Engine")

    tab1, tab2, tab3 = st.tabs(["Settlement schedule", "Cash movements", "Failed settlements"])
    conn = get_conn()

    with tab1:
        st.subheader("Settlement schedule")

        c1, c2, c3, c4 = st.columns(4)
        total = conn.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
        settled = conn.execute("SELECT COUNT(*) FROM settlements WHERE status='Settled'").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM settlements WHERE status='Failed'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM settlements WHERE status='Pending'").fetchone()[0]
        c1.metric("Total due", total)
        c2.metric("Settled", settled)
        c3.metric("Failed", failed)
        c4.metric("Pending", pending)

        df = pd.read_sql("""
            SELECT settlement_id as "ID", trade_id as "Trade ID", ticker as "Ticker",
                   quantity as "Qty", amount as "Amount ($)", due_date as "Due Date",
                   cycle as "Cycle", status as "Status"
            FROM settlements ORDER BY due_date ASC
        """, conn)

        df["Amount ($)"] = df["Amount ($)"].apply(lambda x: f"{x:,.2f}")

        def style_status(val):
            if val == "Settled": return "color: #4caf82"
            if val == "Failed": return "color: #ff6b6b; font-weight:600"
            if val == "Pending": return "color: #f0a030"
            return ""

        st.dataframe(df.style.applymap(style_status, subset=["Status"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Settlement calculator")
        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input("Quantity", min_value=1, value=100)
        with col2:
            price = st.number_input("Price ($)", min_value=0.01, value=194.20)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Settlement amount", f"${qty * price:,.2f}")

    with tab2:
        st.subheader("Cash movement tracker")

        cash_in = conn.execute("SELECT SUM(amount) FROM settlements WHERE status='Settled'").fetchone()[0] or 0
        cash_out = conn.execute("SELECT SUM(amount) FROM settlements").fetchone()[0] or 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Cash in", f"${cash_in:,.2f}", delta=None)
        col2.metric("Cash out (expected)", f"${cash_out:,.2f}", delta=None)
        col3.metric("Net", f"${cash_in - cash_out:,.2f}", delta=None)

        df_cash = pd.DataFrame([
            {"Direction": "Cash In", "Source": "AAPL settlement", "Amount ($)": "97,100.00", "Status": "✅ Received"},
            {"Direction": "Cash In", "Source": "NVDA settlement", "Amount ($)": "177,460.00", "Status": "✅ Received"},
            {"Direction": "Cash In", "Source": "SPY settlement", "Amount ($)": "156,930.00", "Status": "✅ Received"},
            {"Direction": "Cash Out", "Source": "MSFT TRS payment", "Amount ($)": "412,800.00", "Status": "❌ Failed"},
            {"Direction": "Cash Out", "Source": "ES margin call", "Amount ($)": "52,345.00", "Status": "⏳ Pending"},
        ])
        st.dataframe(df_cash, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Failed settlement monitor")

        df_failed = pd.read_sql("""
            SELECT s.settlement_id, s.trade_id, s.ticker, s.amount, s.due_date, s.status,
                   t.counterparty
            FROM settlements s JOIN trades t ON s.trade_id = t.trade_id
            WHERE s.status IN ('Failed', 'Pending')
            ORDER BY s.due_date ASC
        """, conn)

        if df_failed.empty:
            st.success("No failed or pending settlements.")
        else:
            df_failed["amount"] = df_failed["amount"].apply(lambda x: f"${x:,.2f}")
            df_failed.columns = ["ID", "Trade ID", "Ticker", "Amount", "Due Date", "Status", "Counterparty"]

            def style_s(val):
                if val == "Failed": return "color: #ff6b6b; font-weight:600"
                if val == "Pending": return "color: #f0a030"
                return ""

            st.dataframe(df_failed.style.applymap(style_s, subset=["Status"]), use_container_width=True, hide_index=True)

            if st.button("🔔 Escalate all failed settlements"):
                st.warning("Escalation notification sent to Operations Management.")

    conn.close()
