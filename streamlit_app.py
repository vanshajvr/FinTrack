# streamlit_app.py
import streamlit as st
import sqlite3
from datetime import datetime

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

# --- Streamlit app ---
st.title("FinTrack 💰")
st.write("Track your income and expenses easily!")

# Add a transaction
st.subheader("Add Transaction")
with st.form("transaction_form"):
    amount = st.number_input("Amount", min_value=0.0)
    trans_type = st.selectbox("Type", ["income", "expense"])
    category = st.text_input("Category", value="Uncategorized")
    submitted = st.form_submit_button("Add Transaction")
    
    if submitted:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO transactions (amount, type, category, date) VALUES (?, ?, ?, ?)",
            (amount, trans_type, category, date)
        )
        conn.commit()
        st.success("Transaction added!")

# View transactions
st.subheader("All Transactions")
cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
transactions = cursor.fetchall()
for t in transactions:
    st.write(f"{t[4]} - {t[2].capitalize()} - {t[3]} - ₹{t[1]}")

# Summary
st.subheader("Summary")
cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
total_income = cursor.fetchone()[0] or 0
cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
total_expense = cursor.fetchone()[0] or 0
st.write(f"**Total Income:** ₹{total_income}")
st.write(f"**Total Expenses:** ₹{total_expense}")
st.write(f"**Balance:** ₹{total_income - total_expense}")
