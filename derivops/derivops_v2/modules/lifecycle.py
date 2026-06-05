import streamlit as st
import pandas as pd
from utils.db import get_conn

def render():
    st.title("📅 Derivatives Lifecycle")

    tab1, tab2 = st.tabs(["Lifecycle events", "Corporate actions"])
    conn = get_conn()

    with tab1:
        st.subheader("Lifecycle event tracker")

        col1, col2 = st.columns(2)
        with col1:
            products = ["All", "Equity Option", "Equity Future", "Equity Swap"]
            filter_prod = st.selectbox("Filter by product", products)
        with col2:
            statuses = ["All", "Done", "Upcoming", "Pending"]
            filter_status = st.selectbox("Filter by status", statuses)

        query = "SELECT * FROM lifecycle_events WHERE 1=1"
        params = []
        if filter_prod != "All":
            query += " AND product=?"; params.append(filter_prod)
        if filter_status != "All":
            query += " AND status=?"; params.append(filter_status)
        query += " ORDER BY event_date ASC"

        df = pd.read_sql(query, conn, params=params)

        if df.empty:
            st.info("No lifecycle events found.")
        else:
            df_display = df[["trade_id", "product", "ticker", "event_type", "event_date", "status", "notes"]]
            df_display.columns = ["Trade ID", "Product", "Ticker", "Event", "Date", "Status", "Notes"]

            def style_status(val):
                if val == "Done": return "color: #4caf82"
                if val == "Upcoming": return "color: #f0a030; font-weight:600"
                if val == "Pending": return "color: #8899aa"
                return ""

            st.dataframe(df_display.style.map(style_status, subset=["Status"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Add lifecycle event")
        col1, col2, col3 = st.columns(3)
        with col1:
            trade_ids = [r[0] for r in conn.execute("SELECT DISTINCT trade_id FROM trades").fetchall()]
            trade_id = st.selectbox("Trade ID", trade_ids)
            product = st.selectbox("Product", ["Equity Option", "Equity Future", "Equity Swap"])
        with col2:
            ticker = st.text_input("Ticker")
            event_type = st.selectbox("Event type", ["Open", "Expiration", "Exercise", "Reset Date", "Payment Date", "Maturity", "Delivery"])
        with col3:
            import datetime
            event_date = st.date_input("Event date")
            status_lc = st.selectbox("Status", ["Pending", "Upcoming", "Done"])
            notes = st.text_input("Notes")

        if st.button("Add event", type="primary"):
            conn.execute(
                "INSERT INTO lifecycle_events (trade_id, product, ticker, event_type, event_date, status, notes) VALUES (?,?,?,?,?,?,?)",
                (trade_id, product, ticker, event_type, event_date.isoformat(), status_lc, notes)
            )
            conn.commit()
            st.success(f"Lifecycle event **{event_type}** added for {trade_id}.")
            st.rerun()

    with tab2:
        st.subheader("Corporate actions monitor")

        corp_actions = pd.DataFrame([
            {"Ticker": "AAPL", "Event": "Dividend", "Amount": "$0.25/share", "Ex-Date": "2026-06-09", "Impact": "+$125 on 500 shares", "Status": "⏳ Pending"},
            {"Ticker": "NVDA", "Event": "Stock Split 10:1", "Amount": "—", "Ex-Date": "2026-06-12", "Impact": "Position × 10", "Status": "⏳ Pending"},
            {"Ticker": "MSFT", "Event": "Dividend", "Amount": "$0.83/share", "Ex-Date": "2026-05-20", "Impact": "+$830 on 1,000 shares", "Status": "✅ Processed"},
        ])

        def style_corp(val):
            if "Processed" in str(val): return "color: #4caf82"
            if "Pending" in str(val): return "color: #f0a030"
            return ""

        st.dataframe(corp_actions.style.map(style_corp, subset=["Status"]), use_container_width=True, hide_index=True)

        st.info("Corporate actions automatically adjust affected positions upon processing.")

    conn.close()
