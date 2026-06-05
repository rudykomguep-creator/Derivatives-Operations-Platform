import streamlit as st
import pandas as pd
from utils.db import get_conn
from datetime import date, timedelta
import uuid, io

def render():
    st.title("📥 Trade Capture")

    tab1, tab2, tab3 = st.tabs(["Manual entry", "Import CSV / Excel", "Trade repository"])

    # ── Manual Entry ──────────────────────────────────────────
    with tab1:
        st.subheader("New trade entry")
        col1, col2 = st.columns(2)
        with col1:
            product = st.selectbox("Product type", ["Equity", "Equity Option", "Equity Future", "Equity Swap", "Bond"])
            counterparty = st.text_input("Counterparty", placeholder="e.g. Alpha Capital")
            ticker = st.text_input("Ticker", placeholder="e.g. AAPL")
            quantity = st.number_input("Quantity", min_value=1, value=100)
        with col2:
            price = st.number_input("Price", min_value=0.01, value=100.00, step=0.01)
            trade_date = st.date_input("Trade date", value=date.today())
            settlement_date = st.date_input("Settlement date", value=date.today() + timedelta(days=2))
            source = st.selectbox("Source", ["Manual", "FO System", "Bloomberg"])

        trade_id = f"TRD-{date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        st.info(f"Auto-generated Trade ID: **{trade_id}**")

        if st.button("✅ Submit trade", type="primary"):
            if not counterparty or not ticker:
                st.error("Please fill in all required fields.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                    (trade_id, product, counterparty, ticker, quantity, price,
                     trade_date.isoformat(), settlement_date.isoformat(), "Pending", source)
                )
                conn.execute(
                    "INSERT INTO trade_events (trade_id, event_type, description) VALUES (?,?,?)",
                    (trade_id, "Created", f"Trade captured manually — {product} {ticker}")
                )
                conn.commit()
                conn.close()
                st.success(f"Trade **{trade_id}** captured successfully.")
                st.balloons()

    # ── Import ─────────────────────────────────────────────────
    with tab2:
        st.subheader("Import trades from file")
        st.caption("Accepted formats: CSV, Excel (.xlsx). Required columns: product, counterparty, ticker, quantity, price, trade_date, settlement_date")

        uploaded = st.file_uploader("Upload FO trade file", type=["csv", "xlsx"])

        st.markdown("**Expected format:**")
        sample = pd.DataFrame({
            "product": ["Equity", "Equity Option"],
            "counterparty": ["Alpha Capital", "Nexus Securities"],
            "ticker": ["AAPL", "MSFT"],
            "quantity": [500, 200],
            "price": [194.20, 412.80],
            "trade_date": [date.today().isoformat(), date.today().isoformat()],
            "settlement_date": [(date.today()+timedelta(days=2)).isoformat(), (date.today()+timedelta(days=2)).isoformat()],
        })
        st.dataframe(sample, hide_index=True, use_container_width=True)

        # Download sample
        csv_buf = io.StringIO()
        sample.to_csv(csv_buf, index=False)
        st.download_button("⬇ Download sample CSV", csv_buf.getvalue(), "FO_Trades_sample.csv", "text/csv")

        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)

                st.success(f"Loaded **{len(df)} trades** from `{uploaded.name}`")
                st.dataframe(df, use_container_width=True, hide_index=True)

                if st.button("Import all trades", type="primary"):
                    conn = get_conn()
                    imported = 0
                    for _, row in df.iterrows():
                        tid = f"TRD-IMP-{str(uuid.uuid4())[:6].upper()}"
                        try:
                            conn.execute(
                                "INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                                (tid, row["product"], row["counterparty"], row["ticker"],
                                 row["quantity"], row["price"], str(row["trade_date"]),
                                 str(row["settlement_date"]), "Pending", "Import")
                            )
                            imported += 1
                        except Exception:
                            pass
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {imported} trades imported successfully.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # ── Repository ─────────────────────────────────────────────
    with tab3:
        st.subheader("Trade repository")
        conn = get_conn()

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_product = st.selectbox("Filter by product", ["All"] + ["Equity", "Equity Option", "Equity Future", "Equity Swap", "Bond"])
        with col2:
            filter_status = st.selectbox("Filter by status", ["All", "Pending", "Affirmed", "Settled", "Break", "Failed"])
        with col3:
            filter_source = st.selectbox("Filter by source", ["All", "Manual", "FO System", "Import", "FO"])

        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        if filter_product != "All":
            query += " AND product=?"; params.append(filter_product)
        if filter_status != "All":
            query += " AND status=?"; params.append(filter_status)
        if filter_source != "All":
            query += " AND source=?"; params.append(filter_source)
        query += " ORDER BY created_at DESC"

        df = pd.read_sql(query, conn, params=params)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} trades found")

        # Export
        csv = df.to_csv(index=False)
        st.download_button("⬇ Export to CSV", csv, "trades_export.csv", "text/csv")
        conn.close()
