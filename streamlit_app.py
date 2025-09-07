import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ------------------ DATABASE SETUP ------------------ #
DB_FILE = "finance.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in cursor.fetchall()]

    if 'currency' not in columns:
        conn.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR (₹)'")
    if 'notes' not in columns:
        conn.execute("ALTER TABLE transactions ADD COLUMN notes TEXT DEFAULT ''")
    
    conn.execute("""
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

# ------------------ THEME SETTINGS ------------------ #
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "currency" not in st.session_state:
    st.session_state.currency = "INR (₹)"

text_color = "#ffffff" if st.session_state.dark_mode else "#000000"
bg_color = "#1f1f1f" if st.session_state.dark_mode else "#f5f5f5"
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .stSidebar {{
            background-color: {'#2c2c2c' if st.session_state.dark_mode else '#e0e0e0'};
        }}
        .css-1d391kg p {{
            color: {text_color};
        }}
    </style>
    """, unsafe_allow_html=True
)

# ------------------ SIDEBAR NAVIGATION ------------------ #
st.sidebar.markdown("<h1 style='text-align:center;'>FinTrack</h1>", unsafe_allow_html=True)
menu_options = ["Home", "Dashboard", "Add Transaction", "View Transactions"]
menu = st.sidebar.radio("Navigate", menu_options, index=0)

st.sidebar.markdown("---")
# Currency selection
st.sidebar.markdown("### Currency")
currency = st.sidebar.selectbox(
    "",
    ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"],
    index=["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"].index(st.session_state.currency)
)
st.session_state.currency = currency

# Dark/Light toggle
st.sidebar.markdown("---")
st.session_state.dark_mode = st.sidebar.checkbox("Dark Mode", value=st.session_state.dark_mode)

# ------------------ HOME ------------------ #
if menu == "Home":
    st.title("Welcome to FinTrack")
    st.markdown(f"Manage your personal finances efficiently. Current currency: **{st.session_state.currency}**")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions yet. Add your first transaction!")
    else:
        total_income = df[df['type']=='income']['amount'].sum()
        total_expense = df[df['type']=='expense']['amount'].sum()
        balance = total_income - total_expense
        symbol = st.session_state.currency.split()[1]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"{symbol}{total_income:,.2f}")
        col2.metric("Total Expense", f"{symbol}{total_expense:,.2f}")
        col3.metric("Balance", f"{symbol}{balance:,.2f}")

        st.markdown("---")
        # Expense Pie chart
        expense_df = df[df['type']=='expense']
        if not expense_df.empty:
            fig = px.pie(expense_df, names='category', values='amount', title=f"Expense Breakdown ({st.session_state.currency})")
            st.plotly_chart(fig, use_container_width=True)

# ------------------ ADD TRANSACTION ------------------ #
elif menu == "Add Transaction":
    st.title("Add New Transaction")

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=1.0, step=100.0)
        trans_type = st.selectbox("Transaction Type", ["income", "expense"])
    with col2:
        category = st.text_input("Category", "General")
        date = st.date_input("Date", datetime.today())
        notes = st.text_input("Notes", "")

    if st.button("Add Transaction"):
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO transactions (amount, type, category, currency, date, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (amount, trans_type, category, st.session_state.currency, date.strftime("%Y-%m-%d"), notes)
        )
        conn.commit()
        conn.close()
        st.success(f"Transaction added successfully in {st.session_state.currency}!")

# ------------------ DASHBOARD ------------------ #
elif menu == "Dashboard":
    st.title("Finance Dashboard")
    st.markdown(f"Insights into your income and expenses ({st.session_state.currency})")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions yet.")
    else:
        col1, col2, col3 = st.columns(3)
        total_income = df[df['type']=='income']['amount'].sum()
        total_expense = df[df['type']=='expense']['amount'].sum()
        balance = total_income - total_expense
        symbol = st.session_state.currency.split()[1]

        col1.metric("Total Income", f"{symbol}{total_income:,.2f}")
        col2.metric("Total Expense", f"{symbol}{total_expense:,.2f}")
        col3.metric("Balance", f"{symbol}{balance:,.2f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            expense_df = df[df['type']=='expense']
            if not expense_df.empty:
                fig = px.pie(expense_df, names='category', values='amount', title=f"Expense Breakdown ({st.session_state.currency})")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.strftime('%Y-%m')
            monthly_summary = df.groupby(['month','type'])['amount'].sum().reset_index()
            fig2 = px.bar(monthly_summary, x='month', y='amount', color='type', barmode='group', title="Monthly Income vs Expense")
            st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "View Transactions":
    st.title("Transaction History")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
