import streamlit as st
import pandas as pd
from utils.db import get_conn
from datetime import date

def render():
    st.title("⬡ Operations Dashboard")
    st.caption(f"Live view — {date.today().strftime('%B %d, %Y')}")

    conn = get_conn()

    total_trades = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    open_breaks = conn.execute("SELECT COUNT(*) FROM breaks WHERE status != 'Resolved'").fetchone()[0]
    settled = conn.execute("SELECT COUNT(*) FROM settlements WHERE status='Settled'").fetchone()[0]
    total_stl = conn.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
    affirmed = conn.execute("SELECT COUNT(*) FROM trades WHERE status='Affirmed'").fetchone()[0]
    settlement_rate = round((settled / total_stl * 100), 1) if total_stl else 0
    affirmation_rate = round((affirmed / total_trades * 100), 1) if total_trades else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Trades today", total_trades, "+4 vs yesterday")
    with col2:
        st.metric("Open breaks", open_breaks, delta=None)
    with col3:
        st.metric("Settlement rate", f"{settlement_rate}%")
    with col4:
        st.metric("Affirmation rate", f"{affirmation_rate}%")
    with col5:
        failed = conn.execute("SELECT COUNT(*) FROM settlements WHERE status='Failed'").fetchone()[0]
        st.metric("Failed settlements", failed)

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Trades by product")
        df_prod = pd.read_sql("SELECT product, COUNT(*) as count FROM trades GROUP BY product ORDER BY count DESC", conn)
        st.bar_chart(df_prod.set_index("product"), use_container_width=True, height=220)

    with col_b:
        st.subheader("Break severity distribution")
        df_brk = pd.read_sql("SELECT severity, COUNT(*) as count FROM breaks WHERE status != 'Resolved' GROUP BY severity", conn)
        if not df_brk.empty:
            st.bar_chart(df_brk.set_index("severity"), use_container_width=True, height=220)
        else:
            st.success("No open breaks!")

    st.subheader("Recent trades")
    df_trades = pd.read_sql("""
        SELECT trade_id as "Trade ID", product as "Product", counterparty as "Counterparty",
               ticker as "Ticker", quantity as "Qty", price as "Price",
               settlement_date as "Settlement", status as "Status"
        FROM trades ORDER BY created_at DESC LIMIT 8
    """, conn)

    def color_status(val):
        colors = {"Settled": "color: #4caf82", "Break": "color: #ff6b6b",
                  "Affirmed": "color: #5b9bd5", "Pending": "color: #f0a030", "Failed": "color: #ff6b6b"}
        return colors.get(val, "")

    st.dataframe(df_trades.style.applymap(color_status, subset=["Status"]), use_container_width=True, hide_index=True)

    conn.close()
