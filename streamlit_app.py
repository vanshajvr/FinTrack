# streamlit_app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from pathlib import Path

# -------------------------
# Files & DB
# -------------------------
DB_PATH = Path("finance.db")
CSS_PATH = Path("styles.css")

# -------------------------
# Tiny DB helper functions
# -------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
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

def add_transaction(amount, ttype, category, currency, date_str, notes=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO transactions (amount, type, category, currency, date, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (amount, ttype, category, currency, date_str, notes)
        )

def update_transaction(txn_id, amount, ttype, category, currency, date_str, notes):
    with get_conn() as conn:
        conn.execute(
            "UPDATE transactions SET amount=?, type=?, category=?, currency=?, date=?, notes=? WHERE id=?",
            (amount, ttype, category, currency, date_str, notes, txn_id)
        )

def delete_transaction(txn_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))

def load_transactions():
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn, parse_dates=["date"])
    return df

# -------------------------
# App UI helpers
# -------------------------
def inject_css():
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

def header():
    st.markdown(
        """
        <div class="header">
            <div>
                <h1 class="title">💰 FinTrack</h1>
                <p class="tag">Track smarter · Spend wiser · Save faster</p>
            </div>
            <div class="small-meta">v2.0</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def nav_menu():
    choice = st.sidebar.radio(
        "",
        ("🏠 Overview", "➕ Add", "✏️ Edit / Delete", "📜 Transactions"),
        index=0
    )
    st.sidebar.markdown("---")
    # filters in sidebar
    currencies = ["All", "INR", "USD", "EUR", "GBP", "JPY"]
    sel_currency = st.sidebar.selectbox("Show currency", currencies, index=0)
    date_min, date_max = st.sidebar.date_input("Date range",
                                               value=(datetime.today().replace(day=1).date(), datetime.today().date()))
    st.sidebar.markdown("## Quick actions")
    if st.sidebar.button("Export CSV"):
        df_all = load_transactions()
        csv = df_all.to_csv(index=False).encode("utf-8")
        st.sidebar.download_button("Download CSV", csv, "transactions.csv", "text/csv")
    return choice, sel_currency, date_min, date_max

def summary_cards(df):
    if df.empty:
        st.info("No transactions to show. Add your first transaction.")
        return
    # totals per selected currency already filtered upstream
    income = df[df["type"] == "income"]["amount"].sum()
    expense = df[df["type"] == "expense"]["amount"].sum()
    balance = income - expense

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card income"><div class="card-title">Income</div><div class="card-value">₹{income:,.2f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card expense"><div class="card-title">Expense</div><div class="card-value">₹{expense:,.2f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card balance"><div class="card-title">Balance</div><div class="card-value">₹{balance:,.2f}</div></div>', unsafe_allow_html=True)

# -------------------------
# Initialize DB & CSS
# -------------------------
init_db()
inject_css()

# -------------------------
# Page header
# -------------------------
header()

# -------------------------
# Sidebar navigation + filters
# -------------------------
menu_choice, sel_currency, date_min, date_max = nav_menu()

# -------------------------
# Load and filter data
# -------------------------
df = load_transactions()
# ensure date is datetime
if not df.empty:
    df["date"] = pd.to_datetime(df["date"]).dt.date

# apply filters
if sel_currency != "All" and not df.empty:
    df = df[df["currency"] == sel_currency]
if not df.empty:
    df = df[(df["date"] >= date_min) & (df["date"] <= date_max)]

# -------------------------
# MENU: Overview
# -------------------------
if menu_choice == "🏠 Overview":
    st.subheader("Overview")
    # currency selector on top
    col_top = st.columns([3,1])
    if df.empty:
        st.info("No data in the selected range/currency. Add transactions via the Add tab.")
    else:
        # show cards (we'll display values with currency symbol from data if mixed currency show 'Multiple')
        summary_cards(df)

        st.markdown("---")
        # Top categories (Expense)
        left, right = st.columns([2,1])
        with left:
            expense_df = df[df["type"] == "expense"]
            if not expense_df.empty:
                by_cat = expense_df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(8)
                fig = px.bar(by_cat, x="category", y="amount", title="Top Spending Categories", text="amount")
                st.plotly_chart(fig, use_container_width=True)
        with right:
            st.write("Quick stats")
            st.write(f"Transactions: **{len(df)}**")
            st.write(f"Start: **{df['date'].min()}**")
            st.write(f"End: **{df['date'].max()}**")

        st.markdown("---")
        # trend
        trend = df.groupby(["date","currency"], as_index=False)["amount"].sum()
        if not trend.empty:
            fig2 = px.line(trend.sort_values("date"), x="date", y="amount", color="currency", title="Daily Trend by Currency", markers=True)
            st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# MENU: Add
# -------------------------
elif menu_choice == "➕ Add":
    st.subheader("Add transaction")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            amount = st.number_input("Amount", min_value=0.01, format="%.2f")
            ttype = st.selectbox("Type", ["expense","income"])
            category = st.selectbox("Category", ["Food","Transport","Shopping","Bills","Salary","Other"])
        with c2:
            currency = st.selectbox("Currency", ["INR","USD","EUR","GBP","JPY"], index=0)
            date_val = st.date_input("Date", datetime.today())
            notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Add transaction")
        if submitted:
            add_transaction(amount, ttype, category, currency, date_val.strftime("%Y-%m-%d"), notes)
            st.success("Transaction added ✅")

# -------------------------
# MENU: Edit / Delete
# -------------------------
elif menu_choice == "✏️ Edit / Delete":
    st.subheader("Edit or Delete transactions")

    df_all = load_transactions()
    if df_all.empty:
        st.info("No transactions yet.")
    else:
        st.dataframe(df_all[["id","date","type","category","amount","currency","notes"]])
        st.markdown("---")
        sel_id = st.number_input("Enter transaction ID to edit/delete", min_value=1, step=1)
        if sel_id:
            sel_row = df_all[df_all["id"] == sel_id]
            if sel_row.empty:
                st.warning("Transaction ID not found.")
            else:
                row = sel_row.iloc[0]
                with st.form("edit_form"):
                    e_amount = st.number_input("Amount", value=float(row["amount"]))
                    e_type = st.selectbox("Type", ["expense","income"], index=0 if row["type"]=="expense" else 1)
                    e_category = st.text_input("Category", value=row["category"])
                    e_currency = st.selectbox("Currency", ["INR","USD","EUR","GBP","JPY"], index=["INR","USD","EUR","GBP","JPY"].index(row["currency"]))
                    e_date = st.date_input("Date", value=datetime.strptime(row["date"], "%Y-%m-%d"))
                    e_notes = st.text_input("Notes", value=row.get("notes","") or "")
                    save = st.form_submit_button("Save changes")
                    delete = st.form_submit_button("Delete transaction")
                    if save:
                        update_transaction(sel_id, e_amount, e_type, e_category, e_currency, e_date.strftime("%Y-%m-%d"), e_notes)
                        st.success("Updated ✅")
                    if delete:
                        delete_transaction(sel_id)
                        st.success("Deleted ✅")

# -------------------------
# MENU: Transactions
# -------------------------
elif menu_choice == "📜 Transactions":
    st.subheader("All Transactions")
    df_show = load_transactions()
    if df_show.empty:
        st.info("No transactions yet.")
    else:
        st.dataframe(df_show, use_container_width=True)
        st.markdown("---")
        # quick download for current view
        csv = df_show.to_csv(index=False).encode("utf-8")
        st.download_button("Export full CSV", csv, "transactions_all.csv", "text/csv")

# -------------------------
# Footer
# -------------------------
st.markdown("<hr/>", unsafe_allow_html=True)
st.caption("FinTrack — polished demo UI • Built with Streamlit")
