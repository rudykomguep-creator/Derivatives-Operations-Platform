import streamlit as st
import pandas as pd
from utils.db import get_conn
from datetime import date

def render():
    st.title("🔄 Reconciliation")

    tab1, tab2, tab3, tab4 = st.tabs(["Trade recon", "Position recon", "Cash recon", "Break dashboard"])

    conn = get_conn()

    # ── Trade Recon ────────────────────────────────────────────
    with tab1:
        st.subheader("Trade reconciliation — FO vs BO")
        st.caption("Comparing FO trades against simulated BO records")

        # Simulate BO data (slightly off for demo)
        fo_trades = pd.read_sql("SELECT trade_id, ticker, quantity, price, counterparty FROM trades", conn)
        bo_data = fo_trades.copy()
        bo_data.loc[bo_data["trade_id"] == "TRD-003", "quantity"] = 900  # deliberate mismatch
        bo_data.loc[bo_data["trade_id"] == "TRD-007", "price"] = 884.00  # price mismatch

        merged = fo_trades.merge(bo_data, on="trade_id", suffixes=("_fo", "_bo"))
        merged["qty_match"] = merged["quantity_fo"] == merged["quantity_bo"]
        merged["price_match"] = abs(merged["price_fo"] - merged["price_bo"]) < 0.01
        merged["status"] = merged.apply(
            lambda r: "✅ Matched" if r["qty_match"] and r["price_match"] else "❌ Mismatch", axis=1
        )

        display = merged[["trade_id", "ticker_fo", "quantity_fo", "quantity_bo", "price_fo", "price_bo", "status"]]
        display.columns = ["Trade ID", "Ticker", "FO Qty", "BO Qty", "FO Price", "BO Price", "Result"]

        def highlight(val):
            if "Mismatch" in str(val): return "color: #ff6b6b; font-weight: 600"
            if "Matched" in str(val): return "color: #4caf82"
            return ""

        st.dataframe(display.style.applymap(highlight, subset=["Result"]), use_container_width=True, hide_index=True)

        mismatches = len(merged[merged["status"].str.contains("Mismatch")])
        st.metric("Total mismatches", mismatches, delta=None)

    # ── Position Recon ─────────────────────────────────────────
    with tab2:
        st.subheader("Position reconciliation")

        positions = [
            {"Ticker": "AAPL", "FO Position": 500, "BO Position": 450, "Delta": -50},
            {"Ticker": "MSFT", "FO Position": 1000, "BO Position": 1000, "Delta": 0},
            {"Ticker": "NVDA", "FO Position": 200, "BO Position": 200, "Delta": 0},
            {"Ticker": "SPY", "FO Position": 300, "BO Position": 300, "Delta": 0},
            {"Ticker": "GOOG", "FO Position": 150, "BO Position": 150, "Delta": 0},
        ]
        df_pos = pd.DataFrame(positions)
        df_pos["Status"] = df_pos["Delta"].apply(lambda d: "❌ Break" if d != 0 else "✅ Matched")

        for _, row in df_pos.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            with col1:
                st.metric(f"FO — {row['Ticker']}", row["FO Position"])
            with col2:
                st.metric(f"BO — {row['Ticker']}", row["BO Position"])
            with col3:
                st.metric("Delta", row["Delta"])
            with col4:
                if row["Delta"] != 0:
                    st.error(row["Status"])
                else:
                    st.success(row["Status"])

    # ── Cash Recon ─────────────────────────────────────────────
    with tab3:
        st.subheader("Cash reconciliation")

        cash = [
            {"Trade ID": "TRD-001", "Ticker": "AAPL", "Expected ($)": 97100, "Received ($)": 97100, "Delta ($)": 0},
            {"Trade ID": "TRD-003", "Ticker": "MSFT", "Expected ($)": 412800, "Received ($)": 0, "Delta ($)": -412800},
            {"Trade ID": "TRD-004", "Ticker": "NVDA", "Expected ($)": 177460, "Received ($)": 177460, "Delta ($)": 0},
            {"Trade ID": "TRD-006", "Ticker": "SPY", "Expected ($)": 156930, "Received ($)": 150000, "Delta ($)": -6930},
        ]
        df_cash = pd.DataFrame(cash)
        df_cash["Status"] = df_cash["Delta ($)"].apply(
            lambda d: "✅ Matched" if d == 0 else ("❌ Missing" if d == -df_cash.loc[df_cash["Delta ($)"] == d, "Expected ($)"].values[0] else "⚠️ Partial")
        )

        def style_cash(val):
            if isinstance(val, (int, float)) and val < 0: return "color: #ff6b6b; font-weight: 600"
            if "Matched" in str(val): return "color: #4caf82"
            if "Missing" in str(val): return "color: #ff6b6b"
            if "Partial" in str(val): return "color: #f0a030"
            return ""

        st.dataframe(df_cash.style.applymap(style_cash), use_container_width=True, hide_index=True)

        total_breaks = df_cash[df_cash["Delta ($)"] != 0]["Delta ($)"].sum()
        st.metric("Total cash breaks", f"${abs(total_breaks):,.2f}", delta=None)

    # ── Break Dashboard ────────────────────────────────────────
    with tab4:
        st.subheader("Break dashboard")

        col1, col2, col3 = st.columns(3)
        open_b = conn.execute("SELECT COUNT(*) FROM breaks WHERE status='Open'").fetchone()[0]
        review_b = conn.execute("SELECT COUNT(*) FROM breaks WHERE status='In Review'").fetchone()[0]
        resolved_b = conn.execute("SELECT COUNT(*) FROM breaks WHERE status='Resolved'").fetchone()[0]
        with col1: st.metric("Open", open_b)
        with col2: st.metric("In review", review_b)
        with col3: st.metric("Resolved", resolved_b)

        df_breaks = pd.read_sql("""
            SELECT break_id as "Break ID", break_type as "Type", ticker as "Ticker",
                   fo_value as "FO Value", bo_value as "BO Value", delta as "Delta",
                   severity as "Severity", status as "Status", description as "Description"
            FROM breaks ORDER BY
                CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
        """, conn)

        def sev_color(val):
            if val == "High": return "color: #ff6b6b; font-weight:600"
            if val == "Medium": return "color: #f0a030; font-weight:600"
            return "color: #4caf82"

        st.dataframe(
            df_breaks.style.applymap(sev_color, subset=["Severity"]),
            use_container_width=True, hide_index=True
        )

        st.markdown("---")
        st.subheader("Update break status")
        col1, col2, col3 = st.columns(3)
        with col1:
            break_ids = [r[0] for r in conn.execute("SELECT break_id FROM breaks").fetchall()]
            selected_break = st.selectbox("Select break", break_ids)
        with col2:
            new_status = st.selectbox("New status", ["Open", "In Review", "Escalated", "Resolved"])
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Update status", type="primary"):
                conn.execute("UPDATE breaks SET status=? WHERE break_id=?", (new_status, selected_break))
                conn.commit()
                st.success(f"{selected_break} updated to **{new_status}**")
                st.rerun()

    conn.close()
