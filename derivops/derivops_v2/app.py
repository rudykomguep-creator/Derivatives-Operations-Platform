import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="DerivOps — Derivatives Operations Platform",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f1923; }
    [data-testid="stSidebar"] label { color: #c9d4e0 !important; }
    [data-testid="stSidebar"] p { color: #c9d4e0 !important; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

from utils.db import init_db
init_db()

with st.sidebar:
    st.markdown("## ⬡ DerivOps")
    st.markdown("<div style='font-size:11px;color:#556677;margin-bottom:20px'>Derivatives Operations Platform</div>", unsafe_allow_html=True)
    st.markdown("---")
    selection = st.radio("Navigation", [
        "⬡  Operations Dashboard",
        "📥  Trade Capture",
        "🔄  Reconciliation",
        "✅  Trade Affirmation",
        "💰  Settlement Engine",
        "📒  Accounting Engine",
        "📅  Derivatives Lifecycle",
    ], label_visibility="collapsed")

if selection == "⬡  Operations Dashboard":
    from modules import dashboard; dashboard.render()
elif selection == "📥  Trade Capture":
    from modules import trade_capture; trade_capture.render()
elif selection == "🔄  Reconciliation":
    from modules import reconciliation; reconciliation.render()
elif selection == "✅  Trade Affirmation":
    from modules import affirmation; affirmation.render()
elif selection == "💰  Settlement Engine":
    from modules import settlement; settlement.render()
elif selection == "📒  Accounting Engine":
    from modules import accounting; accounting.render()
elif selection == "📅  Derivatives Lifecycle":
    from modules import lifecycle; lifecycle.render()
