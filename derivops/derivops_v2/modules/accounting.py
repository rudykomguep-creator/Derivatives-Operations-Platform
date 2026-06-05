import streamlit as st
import pandas as pd
from utils.db import get_conn

def render():
    st.title("📒 Accounting Engine")

    tab1, tab2 = st.tabs(["Journal entries", "Ledger & validation"])
    conn = get_conn()

    with tab1:
        st.subheader("Journal generator")

        df = pd.read_sql("""
            SELECT entry_id as "Entry ID", trade_id as "Trade ID", account as "Account",
                   debit as "Debit ($)", credit as "Credit ($)", validated as "Valid",
                   created_at as "Timestamp"
            FROM journals ORDER BY entry_id
        """, conn)

        df["Debit ($)"] = df["Debit ($)"].apply(lambda x: f"{x:,.2f}" if x > 0 else "—")
        df["Credit ($)"] = df["Credit ($)"].apply(lambda x: f"{x:,.2f}" if x > 0 else "—")
        df["Valid"] = df["Valid"].apply(lambda x: "✅ Balanced" if x else "❌ Unbalanced")

        def style_valid(val):
            if "Balanced" in str(val): return "color: #4caf82"
            if "Unbalanced" in str(val): return "color: #ff6b6b; font-weight:600"
            return ""

        st.dataframe(df.style.applymap(style_valid, subset=["Valid"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Generate journal entry")

        col1, col2, col3 = st.columns(3)
        with col1:
            trade_ids = [r[0] for r in conn.execute("SELECT trade_id FROM trades").fetchall()]
            trade_id = st.selectbox("Trade ID", trade_ids)
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.01, value=10000.00)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Generate Dr/Cr entries", type="primary"):
                import uuid
                entry_id = f"JNL-{str(uuid.uuid4())[:5].upper()}"
                conn.execute("INSERT INTO journals (entry_id, trade_id, account, debit, credit, validated) VALUES (?,?,?,?,?,?)",
                             (entry_id, trade_id, "Equity Position", amount, 0, 1))
                conn.execute("INSERT INTO journals (entry_id, trade_id, account, debit, credit, validated) VALUES (?,?,?,?,?,?)",
                             (entry_id, trade_id, "Cash", 0, amount, 1))
                conn.commit()
                st.success(f"Journal entry **{entry_id}** created: Dr Equity Position / Cr Cash — ${amount:,.2f}")
                st.rerun()

    with tab2:
        st.subheader("Accounting validation — Debit = Credit check")

        df_val = pd.read_sql("""
            SELECT entry_id,
                   SUM(debit) as total_debit,
                   SUM(credit) as total_credit,
                   ROUND(SUM(debit) - SUM(credit), 2) as difference
            FROM journals GROUP BY entry_id
        """, conn)

        df_val["balanced"] = df_val["difference"] == 0
        df_val["Status"] = df_val["balanced"].apply(lambda x: "✅ Balanced" if x else "❌ Out of balance")

        def style_b(val):
            if "Balanced" in str(val): return "color: #4caf82"
            if "Out of balance" in str(val): return "color: #ff6b6b; font-weight:600"
            return ""

        st.dataframe(df_val.style.applymap(style_b, subset=["Status"]), use_container_width=True, hide_index=True)

        balanced = df_val["balanced"].sum()
        total = len(df_val)
        st.metric("Validation rate", f"{round(balanced/total*100,1)}%" if total else "N/A")

        st.markdown("---")
        st.subheader("Ledger summary")
        df_ledger = pd.read_sql("""
            SELECT account as "Account",
                   ROUND(SUM(debit),2) as "Total Debit ($)",
                   ROUND(SUM(credit),2) as "Total Credit ($)",
                   ROUND(SUM(debit)-SUM(credit),2) as "Net ($)"
            FROM journals GROUP BY account
        """, conn)
        st.dataframe(df_ledger, use_container_width=True, hide_index=True)

    conn.close()
