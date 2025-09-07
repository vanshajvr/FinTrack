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
    # Add currency column if missing
    if 'currency' not in columns:
        conn.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR'")
    # Add notes column if missing
    if 'notes' not in columns:
        conn.execute("ALTER TABLE transactions ADD COLUMN notes TEXT DEFAULT ''")
    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            category TEXT NOT NULL,
            currency TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(
    page_title="FinTrack - Personal Finance App",
    layout="wide",
)

# ------------------ SIDEBAR ------------------ #
st.sidebar.title("FinTrack")
menu = st.sidebar.radio("Navigation", ["Home", "Dashboard", "Add Transaction", "View Transactions"])

# Currency selector
if "currency" not in st.session_state:
    st.session_state.currency = "INR"
currency = st.sidebar.selectbox(
    "Select Currency", ["INR", "USD", "EUR", "GBP"], index=["INR","USD","EUR","GBP"].index(st.session_state.currency)
)
st.session_state.currency = currency

# Dark/Light Mode
if "theme" not in st.session_state:
    st.session_state.theme = "Light"
theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=["Light","Dark"].index(st.session_state.theme))
st.session_state.theme = theme

bg_color = "#1E1E1E" if theme=="Dark" else "#FFFFFF"
text_color = "#FFFFFF" if theme=="Dark" else "#000000"
st.markdown(f"<style>body {{background-color: {bg_color}; color: {text_color}; font-family: 'Segoe UI', sans-serif;}}</style>", unsafe_allow_html=True)

# ------------------ HOME ------------------ #
if menu == "Home":
    st.title("FinTrack - Manage Your Finances Smartly")
    st.markdown("""
    FinTrack helps you track your income and expenses, visualize your spending, and stay on top of your financial goals.
    """)
    # Features cards
    col1, col2, col3 = st.columns(3)
    col1.markdown("**Track Transactions**\nKeep a record of your incomes and expenses.")
    col2.markdown("**Insights & Charts**\nSee how your money flows monthly and by category.")
    col3.markdown("**Multi-Currency & Notes**\nSupport for different currencies and notes for each transaction.")
    st.markdown("---")
    # About Me
    st.subheader("About the Creator")
    st.markdown("""
    **Your Name**  
    B.Tech Student | Aspiring Developer  
    [GitHub](https://github.com/) | [LinkedIn](https://www.linkedin.com/)
    """)

# ------------------ ADD TRANSACTION ------------------ #
elif menu == "Add Transaction":
    st.title("Add New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=1.0, step=10.0)
        trans_type = st.selectbox("Transaction Type", ["income", "expense"])
    with col2:
        category = st.text_input("Category", "General")
        date = st.date_input("Date", datetime.today())
        notes = st.text_area("Notes", "")
    if st.button("Add Transaction"):
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO transactions (amount,type,category,currency,date,notes) VALUES (?,?,?,?,?,?)",
            (amount, trans_type, category, st.session_state.currency, date.strftime("%Y-%m-%d"), notes)
        )
        conn.commit()
        conn.close()
        st.success(f"Transaction added in {st.session_state.currency}.")

# ------------------ DASHBOARD ------------------ #
elif menu == "Dashboard":
    st.title("Finance Dashboard")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    df = df[df["currency"]==st.session_state.currency]
    if df.empty:
        st.info("No transactions yet.")
    else:
        # Metrics
        total_income = df[df['type']=='income']['amount'].sum()
        total_expense = df[df['type']=='expense']['amount'].sum()
        balance = total_income - total_expense
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"{st.session_state.currency} {total_income:,.2f}")
        col2.metric("Total Expense", f"{st.session_state.currency} {total_expense:,.2f}")
        col3.metric("Balance", f"{st.session_state.currency} {balance:,.2f}")
        st.markdown("---")
        # Pie chart for expense by category
        expense_df = df[df['type']=='expense']
        if not expense_df.empty:
            fig = px.pie(expense_df, names='category', values='amount', title="Expense by Category")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        # Bar chart monthly income vs expense
        df['month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
        monthly_summary = df.groupby(['month','type'])['amount'].sum().reset_index()
        fig2 = px.bar(monthly_summary, x='month', y='amount', color='type', barmode='group', title="Monthly Income vs Expense")
        st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "View Transactions":
    st.title("Transaction History")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    df = df[df["currency"]==st.session_state.currency]
    if df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
