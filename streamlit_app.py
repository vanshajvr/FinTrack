import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ------------------ DATABASE SETUP ------------------ #
DB_FILE = "finance.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in cursor.fetchall()]

    if "currency" not in columns:
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
    layout="wide"
)

# ------------------ DARK/LIGHT MODE ------------------ #
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Colors based on mode
if st.session_state.dark_mode:
    bg_color = "#0e1117"
    text_color = "#f0f0f0"
    card_color = "#161b22"
else:
    bg_color = "#f8f9fa"
    text_color = "#111111"
    card_color = "#ffffff"

# ------------------ NAVIGATION ------------------ #
if "page" not in st.session_state:
    st.session_state.page = "Home"

def navigate(page_name):
    st.session_state.page = page_name

# ------------------ CUSTOM CSS ------------------ #
st.markdown(f"""
    <style>
        body {{
            background-color: {bg_color};
            color: {text_color};
            font-family: 'Inter', sans-serif;
        }}

        /* Navbar styling */
        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 32px;
            background-color: {card_color};
            box-shadow: 0px 1px 5px rgba(0, 0, 0, 0.15);
            border-radius: 10px;
            margin-bottom: 25px;
        }}
        .nav-links {{
            display: flex;
            gap: 25px;
        }}
        .nav-button {{
            background-color: transparent;
            color: {text_color};
            font-size: 16px;
            font-weight: 600;
            border: none;
            cursor: pointer;
        }}
        .nav-button:hover {{
            color: #2e89ff;
        }}
        .mode-toggle {{
            background-color: #2e89ff;
            color: white;
            padding: 5px 15px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }}
        .mode-toggle:hover {{
            background-color: #1a6fe3;
        }}
    </style>
""", unsafe_allow_html=True)

# ------------------ NAVBAR ------------------ #
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,2])

with col1:
    if st.button("Home", key="home", use_container_width=True):
        navigate("Home")

with col2:
    if st.button("Add Transaction", key="add", use_container_width=True):
        navigate("Add Transaction")

with col3:
    if st.button("Dashboard", key="dashboard", use_container_width=True):
        navigate("Dashboard")

with col4:
    if st.button("View Transactions", key="view", use_container_width=True):
        navigate("View Transactions")

with col5:
    mode_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"
    if st.button(mode_label, key="dark_toggle", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.experimental_rerun()

st.markdown("---")

# ------------------ HOME ------------------ #
if st.session_state.page == "Home":
    st.title("FinTrack - Personal Finance Dashboard")
    st.subheader("Track. Analyze. Grow.")
    st.write(
        """
        **FinTrack** helps you stay on top of your finances effortlessly.  
        Organize your income and expenses, visualize insights, and make smarter decisions.
        """
    )

    st.markdown("### Features")
    st.markdown("""
    - Add and manage income and expenses easily  
    - Categorize transactions (Salary, Food, Travel, Bills, etc.)
    - Filter transactions by currency
    - View sleek dashboards with interactive graphs
    - Download your transaction history as CSV
    """)

    st.markdown("### About the Creator")
    st.markdown("""
    Built by **[Vanshaj Verma](https://www.linkedin.com/in/vanshajverma60)**  
    Check out the source code on [**GitHub**](https://github.com/vanshajvr)
    """)

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

    currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], index=0)

    if st.button("Save Transaction"):
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
            fig = px.pie(expense_df, names='category', values='amount', hole=0.35,
                         color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_layout(
                paper_bgcolor=card_color,
                plot_bgcolor=card_color,
                font=dict(color=text_color, family="Inter"),
            )
            col1.plotly_chart(fig, use_container_width=True)

        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%Y-%m')
        monthly_summary = df.groupby(['month', 'type'])['amount'].sum().reset_index()
        fig2 = px.bar(
            monthly_summary,
            x='month',
            y='amount',
            color='type',
            barmode='group',
            color_discrete_map={'income':'#2e89ff', 'expense':'#ff5252'}
        )
        fig2.update_layout(
            paper_bgcolor=card_color,
            plot_bgcolor=card_color,
            font=dict(color=text_color, family="Inter")
        )
        col2.plotly_chart(fig2, use_container_width=True)

# ------------------ VIEW TRANSACTIONS ------------------ #
elif st.session_state.page == "View Transactions":
    st.title("Transaction History")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("No transactions found.")
    else:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download CSV", csv, "transactions.csv", "text/csv")
