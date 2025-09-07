import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("fintrack.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT,
    currency TEXT DEFAULT 'INR',
    date TEXT NOT NULL
)
""")
conn.commit()

# -----------------------------
# STREAMLIT CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="FinTrack - Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
)

# -----------------------------
# CUSTOM STYLING
# -----------------------------
st.markdown(
    """
    <style>
        .main {
            background-color: #f8f9fa;
        }
        div[data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: bold;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            height: 40px;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #45a049;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# HEADER
# -----------------------------
st.title("💰 FinTrack")
st.caption("Track your income, expenses, and savings with style 🚀")

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
with st.sidebar:
    st.header("➕ Add Transaction")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    trans_type = st.selectbox("Type", ["Income", "Expense"])
    category = st.selectbox(
        "Category", ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"]
    )
    currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "JPY"])
    date = st.date_input("Date", datetime.today())

    if st.button("Add Transaction"):
        cursor.execute(
            "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
            (amount, trans_type, category, currency, date.strftime("%Y-%m-%d")),
        )
        conn.commit()
        st.success("✅ Transaction added successfully!")

# -----------------------------
# FETCH DATA
# -----------------------------
df = pd.read_sql("SELECT * FROM transactions", conn)

# -----------------------------
# DASHBOARD LAYOUT
# -----------------------------
if not df.empty:
    col1, col2, col3 = st.columns(3)

    total_income = df[df["type"] == "Income"]["amount"].sum()
    total_expense = df[df["type"] == "Expense"]["amount"].sum()
    balance = total_income - total_expense

    col1.metric("💵 Total Income", f"{total_income:.2f}")
    col2.metric("💸 Total Expense", f"{total_expense:.2f}")
    col3.metric("🏦 Balance", f"{balance:.2f}")

    st.markdown("---")

    # -----------------------------
    # TABS FOR VISUALIZATION
    # -----------------------------
    tab1, tab2 = st.tabs(["📊 Dashboard", "📜 Transactions"])

    with tab1:
        col1, col2 = st.columns(2)

        # Income vs Expense Pie Chart
        fig1 = px.pie(
            df,
            names="type",
            values="amount",
            color="type",
            color_discrete_map={"Income": "#00b894", "Expense": "#d63031"},
            title="Income vs Expense",
        )
        col1.plotly_chart(fig1, use_container_width=True)

        # Expense Breakdown by Category
        expense_df = df[df["type"] == "Expense"]
        if not expense_df.empty:
            fig2 = px.bar(
                expense_df,
                x="category",
                y="amount",
                color="category",
                title="Expense Breakdown",
                text_auto=True,
            )
            col2.plotly_chart(fig2, use_container_width=True)
        else:
            col2.info("No expense data yet 🚀")

    with tab2:
        st.dataframe(df, use_container_width=True)

else:
    st.info("No transactions yet. Start adding some from the sidebar!")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey;'>Built with ❤️ using Streamlit</div>",
    unsafe_allow_html=True,
)
