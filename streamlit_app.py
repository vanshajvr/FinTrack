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

# ------------------ STREAMLIT CONFIG ------------------ #
st.set_page_config(
    page_title="FinTrack - Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
)

# ------------------ SIDEBAR ------------------ #
st.sidebar.title("FinTrack")
st.sidebar.markdown("Manage your income and expenses smartly!")

# Currency selector
if "currency" not in st.session_state:
    st.session_state.currency = "INR"
currency = st.sidebar.selectbox(
    "Select Currency", ["INR", "USD", "EUR", "GBP"],
    index=["INR","USD","EUR","GBP"].index(st.session_state.currency)
)
st.session_state.currency = currency
st.markdown(f"""
    <style>
        body {{ background-color: {bg_color}; color: {text_color}; }}
        .stButton>button {{ background-color: {card_color}; color: {text_color}; }}
        .stDataFrame>div {{ background-color: {card_color}; color: {text_color}; }}
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
menu_options = ["Home","Add Transaction","Dashboard","View Transactions"]
menu = st.sidebar.selectbox("Navigate", menu_options)

# ------------------ HOME ------------------ #
if menu == "Home":
    st.title("FinTrack - Your Personal Finance Dashboard")
    st.markdown("""
    **Features:**
    - Add and track your income and expenses
    - Filter transactions by currency
    - View sleek visual dashboards
    - Download transaction history as CSV

    **About the Creator:**
    - Built by [Vanshaj Verma](https://www.linkedin.com/in/vanshajverma60)
    - GitHub: [Your GitHub](https://github.com/vanshajvr)
    """)
    st.markdown("---")

# ------------------ ADD TRANSACTION ------------------ #
# ------------------ ADD TRANSACTION ------------------ #
elif menu == "Add Transaction":
    st.title("Add New Transaction")

    # Predefined categories
    categories = ["Salary", "Food", "Travel", "Entertainment", "Shopping", "Bills", "Health", "General"]

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Amount", min_value=1.0, step=100.0)
        trans_type = st.selectbox("Transaction Type", ["income", "expense"])
    with col2:
        # Category selection with option to add custom
        category_option = st.selectbox("Select Category", categories + ["Other"])
        if category_option == "Other":
            category = st.text_input("Enter Category")
        else:
            category = category_option
        date = st.date_input("Date", datetime.today())

    if st.button("Add Transaction"):
        if not category:
            st.warning("Please enter a category.")
        else:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
                (amount, trans_type, category, st.session_state.currency, date.strftime("%Y-%m-%d")),
            )
            conn.commit()
            conn.close()
            st.success(f"Transaction added successfully in {st.session_state.currency}!")

# ------------------ DASHBOARD ------------------ #
elif menu == "Dashboard":
    st.title("Finance Dashboard")
    st.markdown(f"Visual insights ({st.session_state.currency})")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions yet. Add some to see insights!")
    else:
        col1, col2, col3 = st.columns(3)
        total_income = df[df['type'] == 'income']['amount'].sum()
        total_expense = df[df['type'] == 'expense']['amount'].sum()
        balance = total_income - total_expense

        currency_symbol = st.session_state.currency.split()[0]
        col1.metric("Total Income", f"{currency_symbol}{total_income:,.2f}")
        col2.metric("Total Expense", f"{currency_symbol}{total_expense:,.2f}")
        col3.metric("Balance", f"{currency_symbol}{balance:,.2f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        # Pie chart
        expense_df = df[df['type'] == 'expense']
        if not expense_df.empty:
            fig = px.pie(expense_df, names='category', values='amount',
                         hole=0.3, color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_layout(paper_bgcolor=card_color, plot_bgcolor=card_color,
                              font=dict(color=text_color, family="Arial"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No expense data for selected currency.")

        # Bar chart
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%Y-%m')
        monthly_summary = df.groupby(['month', 'type'])['amount'].sum().reset_index()
        fig2 = px.bar(monthly_summary, x='month', y='amount', color='type',
                      barmode='group', title="Monthly Income vs Expense",
                      color_discrete_map={'income':'#1f77b4', 'expense':'#ff7f0e'})
        fig2.update_layout(paper_bgcolor=card_color, plot_bgcolor=card_color,
                           font=dict(color=text_color, family="Arial"))
        st.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif menu == "View Transactions":
    st.title("Transaction History")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    df = df[df["currency"] == st.session_state.currency]

    if df.empty:
        st.info("No transactions found for selected currency.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
