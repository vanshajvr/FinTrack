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
        conn.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR'")
        conn.commit()
    if 'notes' not in columns:
        conn.execute("ALTER TABLE transactions ADD COLUMN notes TEXT DEFAULT ''")
        conn.commit()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            category TEXT NOT NULL,
            currency TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(
    page_title="FinTrack - Personal Finance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SIDEBAR ------------------ #
st.sidebar.title("FinTrack")
st.sidebar.markdown("Manage your finances professionally.")

# Currency selector
if "currency" not in st.session_state:
    st.session_state.currency = "INR"
currency = st.sidebar.selectbox(
    "Select Currency", ["INR", "USD", "EUR", "GBP"],
    index=["INR","USD","EUR","GBP"].index(st.session_state.currency)
)
st.session_state.currency = currency

# Light/Dark toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
st.session_state.dark_mode = st.sidebar.checkbox("Dark Mode", value=st.session_state.dark_mode)

# Apply theme via CSS
if st.session_state.dark_mode:
    bg_color = "#121212"
    text_color = "#f0f0f0"
    card_color = "#1f1f1f"
else:
    bg_color = "#f9f9f9"
    text_color = "#111111"
    card_color = "#ffffff"

st.markdown(f"""
    <style>
        body {{ background-color: {bg_color}; color: {text_color}; }}
        .stButton>button {{ background-color: {card_color}; color: {text_color}; }}
        .stDataFrame>div {{ background-color: {card_color}; color: {text_color}; }}
    </style>
""", unsafe_allow_html=True)

# Navigation
menu = st.sidebar.radio("Navigate", ["Home","Add Transaction","Dashboard","View Transactions"])

# ------------------ HOME ------------------ #
if menu == "Home":
    st.markdown(f"<h1 style='text-align:center; color:{text_color}'>Welcome to FinTrack</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"""
        <h3 style='color:{text_color}'>Features:</h3>
        <ul style='color:{text_color}'>
            <li>Track your income and expenses</li>
            <li>Visualize your finances with sleek graphs</li>
            <li>Support multiple currencies</li>
            <li>Download transactions as CSV</li>
        </ul>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<p style='text-align:center; color:{text_color}'>Created by: Your Name</p>", unsafe_allow_html=True)

# ------------------ ADD TRANSACTION ------------------ #
elif menu == "Add Transaction":
    st.header("Add New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=1.0, step=100.0)
        trans_type = st.selectbox("Type", ["income","expense"])
    with col2:
        category = st.text_input("Category", "General")
        date_val = st.date_input("Date", datetime.today())
        notes = st.text_input("Notes", "")

    if st.button("Add Transaction"):
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO transactions (amount,type,category,currency,date,notes) VALUES (?,?,?,?,?,?)",
            (amount, trans_type, category, st.session_state.currency, date_val.strftime("%Y-%m-%d"), notes)
        )
        conn.commit()
        conn.close()
        st.success(f"Transaction added in {st.session_state.currency}!")

# ------------------ DASHBOARD ------------------ #
elif menu == "Dashboard":
    st.header("Finance Dashboard")
    df = pd.read_sql_query("SELECT * FROM transactions", get_db_connection())
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions found.")
    else:
        col1, col2, col3 = st.columns(3)
        total_income = df[df["type"]=="income"]["amount"].sum()
        total_expense = df[df["type"]=="expense"]["amount"].sum()
        balance = total_income - total_expense
        currency_symbol = st.session_state.currency

        col1.metric("Total Income", f"{currency_symbol} {total_income:,.2f}")
        col2.metric("Total Expense", f"{currency_symbol} {total_expense:,.2f}")
        col3.metric("Balance", f"{currency_symbol} {balance:,.2f}")

        # Pie chart
        expense_df = df[df["type"]=="expense"]
        if not expense_df.empty:
            fig = px.pie(expense_df, names="category", values="amount",
                         title=f"Expense Breakdown ({st.session_state.currency})")
            fig.update_layout(paper_bgcolor=card_color, plot_bgcolor=card_color,
                              font=dict(color=text_color, family="Arial"))
            st.plotly_chart(fig, use_container_width=True)

        # Monthly bar chart
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")
        monthly_summary = df.groupby(["month","type"])["amount"].sum().reset_index()
        fig2 = px.bar(monthly_summary, x="month", y="amount", color="type",
                      barmode="group", title="Monthly Income vs Expense")
        fig2.update_layout(paper_bgcolor=card_color, plot_bgcolor=card_color,
                           font=dict(color=text_color, family="Arial"))
        st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "View Transactions":
    st.header("Transaction History")
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", get_db_connection())
    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
