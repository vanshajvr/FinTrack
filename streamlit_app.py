import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# ------------------ DATABASE SETUP ------------------ #
DB_FILE = "finance.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            currency TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------ STREAMLIT PAGE CONFIG ------------------ #
st.set_page_config(page_title="FinTrack", layout="wide")

# ------------------ CUSTOM STYLES ------------------ #
st.markdown("""
    <style>
    /* Page background */
    .stApp {
        background-color: #f5f6fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #2f3640;
    }

    /* Headers */
    .stHeader {
        font-size: 36px;
        font-weight: 700;
        color: #2f3640;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #dcdde1;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #40739e;
        color: white;
        font-weight: 600;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='stHeader'>FinTrack - Personal Finance Tracker</h1>", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------ #
st.sidebar.title("Settings")
if "currency" not in st.session_state:
    st.session_state.currency = "INR (₹)"

currency = st.sidebar.selectbox(
    "Choose Currency",
    ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"],
    index=["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"].index(st.session_state.currency)
)
st.session_state.currency = currency

menu = st.sidebar.radio("Navigate", ["Add Transaction", "Dashboard", "View Transactions"])

# ------------------ FUNCTIONS ------------------ #
def add_transaction(amount, ttype, category, currency, date_str, notes):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO transactions (amount, type, category, currency, date, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (amount, ttype, category, currency, date_str, notes)
    )
    conn.commit()
    conn.close()

def get_transactions_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df

def delete_transaction(txn_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
    conn.commit()
    conn.close()

def update_transaction(txn_id, amount, ttype, category, currency, date_str, notes):
    conn = get_db_connection()
    conn.execute("""
        UPDATE transactions
        SET amount=?, type=?, category=?, currency=?, date=?, notes=?
        WHERE id=?
    """, (amount, ttype, category, currency, date_str, notes, txn_id))
    conn.commit()
    conn.close()

# ------------------ ADD TRANSACTION ------------------ #
if menu == "Add Transaction":
    st.header("Add New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=1.0, step=100.0)
        ttype = st.selectbox("Transaction Type", ["income", "expense"])
    with col2:
        category = st.text_input("Category", "General")
        date_val = st.date_input("Date", datetime.today())
        notes = st.text_area("Notes", "")

    if st.button("Add Transaction"):
        add_transaction(amount, ttype, category, st.session_state.currency, date_val.strftime("%Y-%m-%d"), notes)
        st.success(f"Transaction added successfully in {st.session_state.currency}!")

# ------------------ DASHBOARD ------------------ #
elif menu == "Dashboard":
    st.header(f"Dashboard ({st.session_state.currency})")
    df = get_transactions_df()
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions yet. Add some to see insights!")
    else:
        total_income = df[df['type']=="income"]['amount'].sum()
        total_expense = df[df['type']=="expense"]['amount'].sum()
        balance = total_income - total_expense
        currency_symbol = st.session_state.currency.split()[1]

        # Display metrics as cards
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"{currency_symbol}{total_income:,.2f}")
        col2.metric("Total Expense", f"{currency_symbol}{total_expense:,.2f}")
        col3.metric("Balance", f"{currency_symbol}{balance:,.2f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        # Pie chart for expenses
        with col1:
            expense_df = df[df['type']=='expense']
            if not expense_df.empty:
                fig = px.pie(expense_df, names='category', values='amount', title="Expense by Category")
                st.plotly_chart(fig, use_container_width=True)

        # Bar chart for monthly summary
        with col2:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.strftime('%Y-%m')
            monthly_summary = df.groupby(['month','type'])['amount'].sum().reset_index()
            fig2 = px.bar(monthly_summary, x='month', y='amount', color='type', barmode='group', title="Monthly Income vs Expense")
            st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "View Transactions":
    st.header("Transaction History")
    df_all = get_transactions_df()
    df_all = df_all[df_all["currency"] == st.session_state.currency]

    if df_all.empty:
        st.info("No transactions found for the selected currency.")
    else:
        st.dataframe(df_all[["id","date","type","category","amount","currency","notes"]])

        selected_id = st.number_input("Enter Transaction ID to Edit/Delete", min_value=1, step=1)
        if st.button("Delete Transaction"):
            delete_transaction(selected_id)
            st.success(f"Transaction ID {selected_id} deleted!")

        st.markdown("---")
        st.subheader("Edit Transaction")
        txn_to_edit = df_all[df_all["id"]==selected_id]
        if not txn_to_edit.empty:
            row = txn_to_edit.iloc[0]
            edit_amount = st.number_input("Amount", value=row['amount'])
            edit_type = st.selectbox("Type", ["income","expense"], index=0 if row['type']=="income" else 1)
            edit_category = st.text_input("Category", value=row['category'])
            edit_date = st.date_input("Date", pd.to_datetime(row['date']))
            edit_notes = st.text_area("Notes", value=row['notes'] if row['notes'] else "")
            if st.button("Save Changes"):
                update_transaction(selected_id, edit_amount, edit_type, edit_category, st.session_state.currency, edit_date.strftime("%Y-%m-%d"), edit_notes)
                st.success("Transaction updated successfully!")
