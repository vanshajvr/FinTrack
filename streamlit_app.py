import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# --- Page config ---
st.set_page_config(page_title="FinTrack 💰", layout="wide")

# --- Database setup ---
conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
    category TEXT NOT NULL,
    date TEXT NOT NULL
)
""")
conn.commit()

# --- Utility functions ---
def add_transaction(amount, trans_type, category):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO transactions (amount, type, category, date) VALUES (?, ?, ?, ?)",
        (amount, trans_type, category, date)
    )
    conn.commit()

def get_transactions():
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    return cursor.fetchall()

def get_summary():
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = cursor.fetchone()[0] or 0
    balance = total_income - total_expense
    return total_income, total_expense, balance

def get_category_data():
    cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' GROUP BY category")
    data = cursor.fetchall()
    return dict(data)

# --- Sidebar filters ---
st.sidebar.title("FinTrack Controls")
st.sidebar.write("Filter transactions here")
filter_type = st.sidebar.selectbox("Filter by Type", ["All", "income", "expense"])
filter_category = st.sidebar.text_input("Filter by Category (optional)", "")

# --- Main layout ---
col1, col2 = st.columns([2, 1])

# --- Transaction Form ---
with col1:
    st.header("Add Transaction 💳")
    with st.form("transaction_form"):
        amount = st.number_input("Amount", min_value=0.0)
        trans_type = st.selectbox("Type", ["income", "expense"])
        category = st.text_input("Category", "Uncategorized")
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            add_transaction(amount, trans_type, category)
            st.success(f"Added {trans_type} of ₹{amount} in {category}")

# --- Summary ---
with col2:
    st.header("Summary 📊")
    total_income, total_expense, balance = get_summary()
    st.metric("Total Income", f"₹{total_income}")
    st.metric("Total Expenses", f"₹{total_expense}")
    st.metric("Balance", f"₹{balance}")

# --- Transaction Table ---
st.header("Transaction History 📝")
transactions = get_transactions()
df = pd.DataFrame(transactions, columns=["ID", "Amount", "Type", "Category", "Date"])

# Apply filters
if filter_type != "All":
    df = df[df["Type"] == filter_type]
if filter_category.strip() != "":
    df = df[df["Category"].str.contains(filter_category, case=False)]

st.dataframe(df)

# --- Expense Category Pie Chart ---
st.header("Expenses by Category 🥡")
category_data = get_category_data()
if category_data:
    fig, ax = plt.subplots()
    ax.pie(category_data.values(), labels=category_data.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.write("No expense data to display.")
