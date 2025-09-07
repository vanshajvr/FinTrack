import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from forex_python.converter import CurrencyRates

# ------------------ DATABASE SETUP ------------------ #
DB_FILE = "finance.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for existing columns
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in cursor.fetchall()]

    # Add 'currency' if missing
    if 'currency' not in columns:
        try:
            conn.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR (₹)'")
        except sqlite3.OperationalError:
            pass

    # Create table if missing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            currency TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------ STREAMLIT PAGE CONFIG ------------------ #
st.set_page_config(
    page_title="FinTrack - Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
)

# ------------------ SIDEBAR ------------------ #
st.sidebar.title("💼 FinTrack")
st.sidebar.markdown("Manage your **income** and **expenses** smartly!")

# Currency selection
if "currency" not in st.session_state:
    st.session_state.currency = "INR (₹)"

currency = st.sidebar.selectbox(
    "🌍 Choose Currency",
    ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"],
    index=["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"].index(st.session_state.currency)
)
st.session_state.currency = currency

# Fetch currency rates
c = CurrencyRates()
base_currency = "INR"
selected_currency = st.session_state.currency.split()[0]

def convert_currency(amount, from_currency, to_currency):
    try:
        return round(c.convert(from_currency, to_currency, amount), 2)
    except:
        return amount

menu = st.sidebar.radio("Navigate", ["➕ Add Transaction", "📊 Dashboard", "📜 View Transactions"])

# ------------------ ADD TRANSACTION ------------------ #
if menu == "➕ Add Transaction":
    st.title("➕ Add New Transaction")

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("💵 Amount", min_value=1.0, step=100.0)
        trans_type = st.selectbox("Transaction Type", ["income", "expense"])
    with col2:
        category = st.text_input("📂 Category", "General")
        date = st.date_input("📅 Date", datetime.today())

    if st.button("Add Transaction"):
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
            (amount, trans_type, category, st.session_state.currency, date.strftime("%Y-%m-%d")),
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Transaction added successfully in {st.session_state.currency}!")

# ------------------ DASHBOARD ------------------ #
elif menu == "📊 Dashboard":
    st.title("📊 Finance Dashboard")
    st.markdown(f"Visual insights into your **income** and **expenses** ({st.session_state.currency})")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    # Filter selected currency only
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions yet. Add some to see insights!")
    else:
        # Balance cards
        col1, col2, col3 = st.columns(3)
        total_income = df[df['type'] == 'income']['amount'].sum()
        total_expense = df[df['type'] == 'expense']['amount'].sum()
        balance = total_income - total_expense
        currency_symbol = st.session_state.currency.split()[1]

        col1.metric("💰 Total Income", f"{currency_symbol}{total_income:,.2f}")
        col2.metric("💸 Total Expense", f"{currency_symbol}{total_expense:,.2f}")
        col3.metric("🏦 Balance", f"{currency_symbol}{balance:,.2f}")

        # Alert if overspending
        if total_expense > total_income:
            st.error("⚠️ Your expenses exceed your income! Time to budget better.")

        st.markdown("---")

        # ------------------ Advanced Filters ------------------ #
        with st.expander("🔍 Apply Filters"):
            col1, col2, col3, col4 = st.columns(4)
            categories = df["category"].unique()
            selected_category = col1.multiselect("Filter by Category", categories, default=list(categories))
            types = col2.multiselect("Filter by Type", ["income", "expense"], default=["income", "expense"])
            min_date = col3.date_input("Start Date", pd.to_datetime(df["date"]).min())
            max_date = col4.date_input("End Date", pd.to_datetime(df["date"]).max())

            df = df[
                (df["category"].isin(selected_category)) &
                (df["type"].isin(types)) &
                (pd.to_datetime(df["date"]) >= pd.to_datetime(min_date)) &
                (pd.to_datetime(df["date"]) <= pd.to_datetime(max_date))
            ]

        # ------------------ Charts ------------------ #
        col1, col2 = st.columns(2)
        with col1:
            expense_df = df[df['type'] == 'expense']
            if not expense_df.empty:
                fig = px.pie(
                    expense_df,
                    names='category',
                    values='amount',
                    title=f"Expense Breakdown by Category ({st.session_state.currency})"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No expense data available for the selected currency.")

        with col2:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.strftime('%Y-%m')
            monthly_summary = df.groupby(['month', 'type'])['amount'].sum().reset_index()

            fig2 = px.bar(
                monthly_summary,
                x='month',
                y='amount',
                color='type',
                title="Monthly Income vs Expense",
                barmode='group'
            )
            st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "📜 View Transactions":
    st.title("📜 Transaction History")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions found for the selected currency.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download CSV (Filtered)",
            csv,
            "transactions.csv",
            "text/csv",
            key='download-csv'
        )
