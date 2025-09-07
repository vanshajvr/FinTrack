import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("fintrack.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT,
    currency TEXT DEFAULT 'INR',
    date TEXT NOT NULL
)
""")
conn.commit()

# -----------------------------
# STREAMLIT CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="FinTrack Dashboard",
    page_icon="💰",
    layout="wide",
)

# -----------------------------
# CUSTOM PREMIUM STYLING
# -----------------------------
st.markdown(
    """
    <style>
        /* Background */
        .main {
            background-color: #f7f9fc;
            font-family: 'Segoe UI', sans-serif;
        }

        /* Cards for metrics */
        .card {
            padding: 20px;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        /* Buttons */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            height: 42px;
            font-size: 16px;
            border: none;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #43a047;
            transform: scale(1.03);
        }

        /* Headings */
        h1, h2, h3 {
            color: #2c3e50;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 10px;
            font-size: 14px;
            color: grey;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# HEADER
# -----------------------------
st.title("💰 FinTrack Dashboard")
st.caption("Manage your finances with insights, trends, and analytics 🚀")

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
with st.sidebar:
    st.header("➕ Add Transaction")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    trans_type = st.selectbox("Type", ["Income", "Expense"])
    category = st.selectbox(
        "Category", ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"]
    )
    currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "JPY"])
    date = st.date_input("Date", datetime.today())

    if st.button("Add Transaction"):
        cursor.execute(
            "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
            (amount, trans_type, category, currency, date.strftime("%Y-%m-%d")),
        )
        conn.commit()
        st.success("✅ Transaction added successfully!")

# -----------------------------
# FETCH DATA
# -----------------------------
df = pd.read_sql("SELECT * FROM transactions", conn)

# -----------------------------
# DASHBOARD LAYOUT
# -----------------------------
if not df.empty:
    # -----------------------------
    # METRICS CARDS
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    total_income = df[df["type"] == "Income"]["amount"].sum()
    total_expense = df[df["type"] == "Expense"]["amount"].sum()
    balance = total_income - total_expense

    with col1:
        st.markdown(f"""
            <div class="card">
                <h3>💵 Total Income</h3>
                <h2 style="color:#2ecc71;">{total_income:.2f} {df['currency'].iloc[-1]}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="card">
                <h3>💸 Total Expense</h3>
                <h2 style="color:#e74c3c;">{total_expense:.2f} {df['currency'].iloc[-1]}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="card">
                <h3>🏦 Balance</h3>
                <h2 style="color:#3498db;">{balance:.2f} {df['currency'].iloc[-1]}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------------
    # FILTERS
    # -----------------------------
    st.subheader("🔍 Filter Data")
    col1, col2 = st.columns(2)
    with col1:
        month_filter = st.selectbox(
            "Select Month",
            ["All"] + sorted(df["date"].apply(lambda x: x[:7]).unique().tolist())
        )
    with col2:
        type_filter = st.multiselect(
            "Select Transaction Type",
            options=df["type"].unique(),
            default=df["type"].unique()
        )

    filtered_df = df.copy()
    if month_filter != "All":
        filtered_df = filtered_df[filtered_df["date"].str.startswith(month_filter)]
    filtered_df = filtered_df[filtered_df["type"].isin(type_filter)]

    # -----------------------------
    # TABS FOR VISUALIZATION
    # -----------------------------
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "📜 Transactions"])

    # -----------------------------
    # TAB 1: Overview
    # -----------------------------
    with tab1:
        col1, col2 = st.columns(2)

        # Income vs Expense Pie Chart
        fig1 = px.pie(
            filtered_df,
            names="type",
            values="amount",
            color="type",
            color_discrete_map={"Income": "#27ae60", "Expense": "#e74c3c"},
            title="Income vs Expense Distribution",
        )
        col1.plotly_chart(fig1, use_container_width=True)

        # Expense Breakdown by Category
        expense_df = filtered_df[filtered_df["type"] == "Expense"]
        if not expense_df.empty:
            fig2 = px.bar(
                expense_df,
                x="category",
                y="amount",
                color="category",
                title="Expense Breakdown by Category",
                text_auto=True,
            )
            col2.plotly_chart(fig2, use_container_width=True)
        else:
            col2.info("No expense data available 🚀")

    # -----------------------------
    # TAB 2: Trends
    # -----------------------------
    with tab2:
        df_sorted = filtered_df.sort_values(by="date")
        fig3 = px.line(
            df_sorted,
            x="date",
            y="amount",
            color="type",
            markers=True,
            title="Transaction Trends Over Time"
        )
        st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # TAB 3: Transactions Table
    # -----------------------------
    with tab3:
        st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("No transactions yet. Start adding some from the sidebar!")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown(
    "<div class='footer'>💻 Built with ❤️ using Streamlit | FinTrack © 2025</div>",
    unsafe_allow_html=True,
)
