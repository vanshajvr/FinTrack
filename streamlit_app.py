import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ------------------ LOAD ENVIRONMENT VARIABLES ------------------ #
load_dotenv()
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

# PostgreSQL connection string
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine (connection pooling enabled)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ------------------ INITIALIZE DATABASE ------------------ #
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                category TEXT NOT NULL,
                currency TEXT NOT NULL,
                date DATE NOT NULL
            )
        """))

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

if "currency" not in st.session_state:
    st.session_state.currency = "INR (₹)"

currency = st.sidebar.selectbox(
    "🌍 Choose Currency",
    ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"],
    index=["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"].index(st.session_state.currency)
)
st.session_state.currency = currency

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
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO transactions (amount, type, category, currency, date)
                VALUES (:amount, :type, :category, :currency, :date)
            """), {
                "amount": amount,
                "type": trans_type,
                "category": category,
                "currency": st.session_state.currency,
                "date": date
            })
        st.success(f"✅ Transaction added successfully in {st.session_state.currency}!")

# ------------------ DASHBOARD ------------------ #
elif menu == "📊 Dashboard":
    st.title("📊 Finance Dashboard")
    st.markdown(f"Visual insights into your **income** and **expenses** ({st.session_state.currency})")

    df = pd.read_sql("SELECT * FROM transactions", engine)

    # Filter only for selected currency
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions yet. Add some to see insights!")
    else:
        col1, col2, col3 = st.columns(3)
        total_income = df[df['type'] == 'income']['amount'].sum()
        total_expense = df[df['type'] == 'expense']['amount'].sum()
        balance = total_income - total_expense

        currency_symbol = st.session_state.currency.split()[1]
        col1.metric("💰 Total Income", f"{currency_symbol}{total_income:,.2f}")
        col2.metric("💸 Total Expense", f"{currency_symbol}{total_expense:,.2f}")
        col3.metric("🏦 Balance", f"{currency_symbol}{balance:,.2f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        # Pie chart by category
        with col1:
            expense_df = df[df['type'] == 'expense']
            if not expense_df.empty:
                fig = px.pie(
                    expense_df,
                    names='category',
                    values='amount',
                    title=f"Expense Breakdown by Category ({st.session_state.currency})",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No expense data available for the selected currency.")

        # Bar chart by month
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
                barmode='group',
            )
            st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "📜 View Transactions":
    st.title("📜 Transaction History")

    df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC", engine)
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions found for the selected currency.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download CSV",
            csv,
            "transactions.csv",
            "text/csv",
            key='download-csv'
        )
