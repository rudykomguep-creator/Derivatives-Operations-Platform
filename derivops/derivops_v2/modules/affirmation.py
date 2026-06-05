import streamlit as st
import pandas as pd
from utils.db import get_conn

def render():
    st.title("✅ Trade Affirmation")

    tab1, tab2 = st.tabs(["Matching engine", "Exception queue"])
    conn = get_conn()

    with tab1:
        st.subheader("Counterparty matching")
        st.caption("Comparing internal trades against simulated counterparty confirmations")

        trades = pd.read_sql("SELECT trade_id, counterparty, ticker, quantity, price FROM trades", conn)

        # Simulate counterparty data with intentional mismatches
        ctp = trades.copy()
        ctp.loc[ctp["trade_id"] == "TRD-003", "quantity"] = 900
        ctp.loc[ctp["trade_id"] == "TRD-007", "price"] = 884.00

        merged = trades.merge(ctp, on="trade_id", suffixes=("_rbc", "_ctp"))
        merged["qty_ok"] = merged["quantity_rbc"] == merged["quantity_ctp"]
        merged["price_ok"] = abs(merged["price_rbc"] - merged["price_ctp"]) < 0.01
        merged["matched"] = merged["qty_ok"] & merged["price_ok"]
        merged["result"] = merged["matched"].apply(lambda x: "✅ Matched" if x else "❌ Unmatched")
        merged["issue"] = merged.apply(lambda r: (
            "Qty mismatch" if not r["qty_ok"] else
            "Price mismatch" if not r["price_ok"] else ""
        ), axis=1)

        display = merged[["trade_id", "counterparty_rbc", "ticker_rbc", "quantity_rbc", "quantity_ctp", "price_rbc", "price_ctp", "result", "issue"]]
        display.columns = ["Trade ID", "Counterparty", "Ticker", "Our Qty", "CTP Qty", "Our Price", "CTP Price", "Result", "Issue"]

        def style_result(val):
            if "Unmatched" in str(val): return "color: #ff6b6b; font-weight:600"
            if "Matched" in str(val): return "color: #4caf82"
            return ""

        st.dataframe(display.style.applymap(style_result, subset=["Result"]), use_container_width=True, hide_index=True)

        matched = merged["matched"].sum()
        unmatched = len(merged) - matched
        c1, c2, c3 = st.columns(3)
        c1.metric("Matched", int(matched))
        c2.metric("Unmatched", int(unmatched))
        c3.metric("Affirmation rate", f"{round(matched/len(merged)*100,1)}%")

    with tab2:
        st.subheader("Exception queue — pending affirmation")

        exceptions = [
            {"Trade ID": "TRD-003", "Counterparty": "Nexus Securities", "Ticker": "MSFT", "Issue": "Qty mismatch (1000 vs 900)", "Since": "09:14", "Priority": "High"},
            {"Trade ID": "TRD-007", "Counterparty": "Citrine Trading", "Ticker": "NVDA", "Issue": "Price mismatch ($887.30 vs $884.00)", "Since": "10:02", "Priority": "Medium"},
        ]
        df_exc = pd.DataFrame(exceptions)

        def style_priority(val):
            if val == "High": return "color: #ff6b6b; font-weight:600"
            if val == "Medium": return "color: #f0a030; font-weight:600"
            return "color: #4caf82"

        st.dataframe(df_exc.style.applymap(style_priority, subset=["Priority"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Affirm a trade manually")
        col1, col2 = st.columns(2)
        with col1:
            trade_ids = [r[0] for r in conn.execute("SELECT trade_id FROM trades").fetchall()]
            t = st.selectbox("Trade ID", trade_ids)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Mark as affirmed", type="primary"):
                conn.execute("UPDATE trades SET status='Affirmed' WHERE trade_id=?", (t,))
                conn.commit()
                st.success(f"Trade {t} marked as **Affirmed**.")

    conn.close()
