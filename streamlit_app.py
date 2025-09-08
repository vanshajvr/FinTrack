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

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(
    page_title="FinTrack - Personal Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

# ------------------ SITE COLORS & FONTS ------------------ #
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Dark/Light toggle in top-right corner
st.session_state.dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")

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
        body {{ background-color: {bg_color}; color: {text_color}; font-family: 'Arial', sans-serif; }}
        .stButton>button {{ background-color: {card_color}; color: {text_color}; border-radius: 5px; }}
        .stDataFrame>div {{ background-color: {card_color}; color: {text_color}; }}
        h1, h2, h3, h4 {{ color: {text_color}; }}
        .navbar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 10px 0;
            background-color: {card_color};
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .nav-link {{
            cursor: pointer;
            font-weight: bold;
            color: {text_color};
        }}
        .nav-link:hover {{
            text-decoration: underline;
        }}
    </style>
""", unsafe_allow_html=True)

# ------------------ NAVIGATION ------------------ #
# Simple single-page navigation using session_state
if "page" not in st.session_state:
    st.session_state.page = "Home"

def navigate(page_name):
    st.session_state.page = page_name

# Top navbar
st.markdown(f"""
<div class="navbar">
    <span class="nav-link" onclick="window.location.reload();">{'Home'}</span>
    <span class="nav-link" onclick="window.location.reload();">{'Add Transaction'}</span>
    <span class="nav-link" onclick="window.location.reload();">{'Dashboard'}</span>
    <span class="nav-link" onclick="window.location.reload();">{'View Transactions'}</span>
</div>
""", unsafe_allow_html=True)

# For actual navigation, we'll use selectbox as hidden
page_select = st.selectbox("", ["Home", "Add Transaction", "Dashboard", "View Transactions"], index=["Home", "Add Transaction", "Dashboard", "View Transactions"].index(st.session_state.page), key="page_select", label_visibility="collapsed")
st.session_state.page = page_select

# ------------------ HOME ------------------ #
if st.session_state.page == "Home":
    st.title("FinTrack - Your Personal Finance Dashboard")
    st.markdown("""
    **Features:**
    - Add and track your income and expenses
    - Categorize transactions (Salary, Food, Travel, etc.)
    - Filter transactions by currency
    - Visual dashboards for insights
    - Download transaction history as CSV

    **About the Creator:**
    - Built by [Vanshaj Verma](https://www.linkedin.com/in/vanshajverma60)
    - GitHub: [vanshajvr](https://github.com/vanshajvr)
    """)
    st.markdown("---")

# ------------------ ADD TRANSACTION ------------------ #
elif st.session_state.page == "Add Transaction":
    st.title("Add New Transaction")

    categories = ["Salary", "Food", "Travel", "Entertainment", "Shopping", "Bills", "Health", "General"]

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=1.0, step=100.0)
        trans_type = st.selectbox("Transaction Type", ["income", "expense"])
    with col2:
        category_option = st.selectbox("Select Category", categories + ["Other"])
        if category_option == "Other":
            category = st.text_input("Enter Category")
        else:
            category = category_option
        date = st.date_input("Date", datetime.today())
    
    # Currency selector
    currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], index=0)

    if st.button("Add Transaction"):
        if not category:
            st.warning("Please enter a category.")
        else:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
                (amount, trans_type, category, currency, date.strftime("%Y-%m-%d")),
            )
            conn.commit()
            conn.close()
            st.success(f"Transaction added successfully in {currency}!")

# ------------------ DASHBOARD ------------------ #
elif st.session_state.page == "Dashboard":
    st.title("Finance Dashboard")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    if df.empty:
        st.info("No transactions yet. Add some to see insights!")
    else:
        col1, col2, col3 = st.columns(3)
        total_income = df[df['type'] == 'income']['amount'].sum()
        total_expense = df[df['type'] == 'expense']['amount'].sum()
        balance = total_income - total_expense

        col1.metric("Total Income", f"{total_income:,.2f}")
        col2.metric("Total Expense", f"{total_expense:,.2f}")
        col3.metric("Balance", f"{balance:,.2f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        expense_df = df[df['type'] == 'expense']
        if not expense_df.empty:
            fig = px.pie(expense_df, names='category', values='amount', hole=0.3,
                         color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_layout(paper_bgcolor=card_color, plot_bgcolor=card_color,
                              font=dict(color=text_color, family="Arial"))
            st.plotly_chart(fig, use_container_width=True)

        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%Y-%m')
        monthly_summary = df.groupby(['month', 'type'])['amount'].sum().reset_index()
        fig2 = px.bar(monthly_summary, x='month', y='amount', color='type', barmode='group',
                      color_discrete_map={'income':'#1f77b4', 'expense':'#ff7f0e'})
        fig2.update_layout(paper_bgcolor=card_color, plot_bgcolor=card_color,
                           font=dict(color=text_color, family="Arial"))
        st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif st.session_state.page == "View Transactions":
    st.title("Transaction History")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
