import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", 5432)

# -----------------------------
# PostgreSQL Connection
# -----------------------------
@st.cache_resource
def get_engine():
    return create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = get_engine()

# -----------------------------
# Create table if not exists
# -----------------------------
def init_db():
    query = """
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        amount NUMERIC NOT NULL,
        type VARCHAR(10) NOT NULL,
        category VARCHAR(50),
        currency VARCHAR(10),
        date DATE DEFAULT CURRENT_DATE
    );
    """
    with engine.connect() as conn:
        conn.execute(query)
init_db()

# -----------------------------
# Helper Functions
# -----------------------------
def insert_transaction(amount, trans_type, category, currency, date):
    query = """
    INSERT INTO transactions (amount, type, category, currency, date)
    VALUES (%s, %s, %s, %s, %s);
    """
    with engine.connect() as conn:
        conn.execute(query, (amount, trans_type, category, currency, date))

def get_transactions():
    query = "SELECT * FROM transactions ORDER BY date DESC;"
    return pd.read_sql(query, engine)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="FinTrack - Expense Tracker", layout="wide")
st.title("💰 FinTrack — Personal Finance Dashboard")

# Sidebar for adding transactions
st.sidebar.header("➕ Add New Transaction")
amount = st.sidebar.number_input("Amount", min_value=0.0, format="%.2f")
trans_type = st.sidebar.selectbox("Type", ["Income", "Expense"])
category = st.sidebar.selectbox(
    "Category",
    ["Salary", "Business", "Food", "Travel", "Shopping", "Bills", "Others"]
)
currency = st.sidebar.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "JPY"])
date = st.sidebar.date_input("Date", datetime.today())

if st.sidebar.button("Add Transaction"):
    insert_transaction(amount, trans_type, category, currency, date)
    st.sidebar.success("✅ Transaction Added Successfully!")

# Fetch data from DB
df = get_transactions()

# -----------------------------
# Dashboard
# -----------------------------
if not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        total_income = df[df["type"] == "Income"]["amount"].sum()
        st.metric("💵 Total Income", f"{total_income:.2f}")
    with col2:
        total_expense = df[df["type"] == "Expense"]["amount"].sum()
        st.metric("💸 Total Expenses", f"{total_expense:.2f}")
    with col3:
        balance = total_income - total_expense
        st.metric("🏦 Current Balance", f"{balance:.2f}")

    # Group by category
    fig1 = px.pie(df[df["type"] == "Expense"], values="amount", names="category",
                  title="Expense Distribution by Category")
    st.plotly_chart(fig1, use_container_width=True)

    # Trend over time
    df["date"] = pd.to_datetime(df["date"])
    fig2 = px.line(df, x="date", y="amount", color="type",
                   title="Transaction Trend Over Time")
    st.plotly_chart(fig2, use_container_width=True)

    # Show table
    st.subheader("📄 Transaction History")
    st.dataframe(df)

else:
    st.info("No transactions yet. Add one from the sidebar!")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("🚀 Built with Streamlit + PostgreSQL | FinTrack")
