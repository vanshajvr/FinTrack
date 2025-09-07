import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="FinTrack", page_icon="💰", layout="wide")

# ------------------ DATABASE SETUP ------------------
conn = sqlite3.connect("transactions.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    type TEXT,
    category TEXT,
    currency TEXT,
    date TEXT
)
""")
conn.commit()

# ------------------ HELPER FUNCTIONS ------------------
def add_transaction(amount, trans_type, category, currency, date):
    c.execute(
        "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
        (amount, trans_type, category, currency, date)
    )
    conn.commit()

def get_all_transactions():
    return pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)

def get_totals_by_currency():
    return pd.read_sql_query(
        "SELECT currency, SUM(amount) as total FROM transactions GROUP BY currency", conn
    )

def get_expense_by_category():
    return pd.read_sql_query(
        "SELECT category, SUM(amount) as total FROM transactions WHERE type='Expense' GROUP BY category", conn
    )

# ------------------ SIDEBAR ------------------
st.sidebar.title("⚙️ Settings")
st.sidebar.info("Manage your personal finance with **FinTrack** 💸")

# ------------------ MAIN TABS ------------------
tab1, tab2, tab3 = st.tabs(["➕ Add Transaction", "📜 Transactions", "📊 Insights"])

# ------------------ TAB 1: ADD TRANSACTION ------------------
with tab1:
    st.subheader("➕ Add New Transaction")

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        trans_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
        category = st.selectbox(
            "Category",
            ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Salary", "Other"]
        )

    with col2:
        currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "JPY"])
        date = st.date_input("Date", datetime.today())

    if st.button("💾 Save Transaction", use_container_width=True):
        if amount > 0:
            add_transaction(amount, trans_type, category, currency, date.strftime("%Y-%m-%d"))
            st.success("✅ Transaction added successfully!")
        else:
            st.error("❌ Please enter a valid amount.")

# ------------------ TAB 2: VIEW TRANSACTIONS ------------------
with tab2:
    st.subheader("📜 All Transactions")

    df = get_all_transactions()
    if df.empty:
        st.info("No transactions yet. Add some from the **Add Transaction** tab.")
    else:
        st.dataframe(df, use_container_width=True)

        # Show totals per currency
        totals_df = get_totals_by_currency()
        st.subheader("💰 Total by Currency")
        cols = st.columns(len(totals_df))
        for i, row in totals_df.iterrows():
            with cols[i]:
                st.metric(label=row["currency"], value=f"{row['total']:.2f}")

# ------------------ TAB 3: INSIGHTS ------------------
with tab3:
    st.subheader("📊 Financial Insights")

    df = get_all_transactions()
    if df.empty:
        st.info("No data to analyze yet.")
    else:
        # Expense by category
        expense_df = get_expense_by_category()
        if not expense_df.empty:
            fig = px.pie(expense_df, names="category", values="total", title="Expenses by Category")
            st.plotly_chart(fig, use_container_width=True)

        # Trend over time
        trend_df = df.groupby(["date", "currency"])["amount"].sum().reset_index()
        fig2 = px.line(trend_df, x="date", y="amount", color="currency", title="Spending Trend Over Time")
        st.plotly_chart(fig2, use_container_width=True)

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown("💡 **FinTrack** — Smart way to track your expenses 💸")
