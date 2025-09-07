# streamlit_app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, date
from typing import Tuple, Dict

# Try to import forex converter; if not available, we'll degrade gracefully
try:
    from forex_python.converter import CurrencyRates, RatesNotAvailableError
    FOREX_AVAILABLE = True
    _c = CurrencyRates()
except Exception:
    FOREX_AVAILABLE = False
    _c = None

# ------------------ CONFIG ------------------ #
DB_FILE = "finance.db"
CURRENCY_CHOICES = [
    ("INR (₹)", "INR", "₹"),
    ("USD ($)", "USD", "$"),
    ("EUR (€)", "EUR", "€"),
    ("GBP (£)", "GBP", "£"),
    ("JPY (¥)", "JPY", "¥"),
]

LABEL_TO_CODE = {label: code for (label, code, sym) in CURRENCY_CHOICES}
LABEL_TO_SYMBOL = {label: sym for (label, code, sym) in CURRENCY_CHOICES}
CODES = [code for (_, code, _) in CURRENCY_CHOICES]
LABELS = [label for (label, _, _) in CURRENCY_CHOICES]

# ------------------ DB HELPERS ------------------ #
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create or migrate DB to include 'currency' column safely."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # If table doesn't exist create it with currency column
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            CREATE TABLE transactions (
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
        return

    # If table exists, check columns and add currency if missing
    cursor.execute("PRAGMA table_info(transactions)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'currency' not in cols:
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR (₹)'")
            conn.commit()
        except sqlite3.OperationalError:
            # If for some reason ALTER fails, ignore (we'll assume column exists)
            pass

    conn.close()

init_db()

# ------------------ FOREX HELPERS ------------------ #
@st.cache_data(ttl=3600)
def fetch_rate(from_code: str, to_code: str) -> float:
    """Fetch single conversion rate. Cached for 1 hour. Return 1.0 on error."""
    if not FOREX_AVAILABLE:
        return 1.0
    try:
        rate = _c.get_rate(from_code, to_code)
        if rate is None:
            return 1.0
        return float(rate)
    except Exception:
        return 1.0

def convert_amount(amount: float, from_label: str, to_label: str) -> float:
    """Convert amount stored in from_label currency to to_label currency using codes."""
    from_code = LABEL_TO_CODE.get(from_label, from_label.split()[0])
    to_code = LABEL_TO_CODE.get(to_label, to_label.split()[0])
    if from_code == to_code:
        return amount
    rate = fetch_rate(from_code, to_code)
    try:
        return round(amount * rate, 2)
    except Exception:
        return amount

# ------------------ STREAMLIT PAGE CONFIG ------------------ #
st.set_page_config(page_title="FinTrack • Dashboard", page_icon="💰", layout="wide")

st.sidebar.title("💼 FinTrack")
st.sidebar.markdown("Manage your **income** and **expenses** smartly — now with multi-currency support!")

# Persist selected UI currency in session_state
if "ui_currency" not in st.session_state:
    st.session_state.ui_currency = "INR (₹)"

# Top-level UI currency selector (affects view/conversion)
st.sidebar.markdown("### Display currency")
st.session_state.ui_currency = st.sidebar.selectbox("View amounts in:", LABELS, index=LABELS.index(st.session_state.ui_currency))

# Add transaction quick defaults
st.sidebar.markdown("---")
st.sidebar.write("Tip: Add transactions from the 'Add Transaction' page.")

menu = st.sidebar.radio("Navigate", ["➕ Add Transaction", "📊 Dashboard", "📜 Transactions"])

# ------------------ ADD TRANSACTION ------------------ #
if menu == "➕ Add Transaction":
    st.title("➕ Add New Transaction")
    with st.form("add_txn_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            trans_type = st.selectbox("Type", ["income", "expense"])
        with col2:
            category = st.text_input("Category", value="General")
            txn_date = st.date_input("Date", value=date.today())
        with col3:
            txn_currency = st.selectbox("Currency", LABELS, index=LABELS.index(st.session_state.ui_currency))
            submit = st.form_submit_button("Add Transaction")

        if submit:
            # Validate
            if amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO transactions (amount, type, category, currency, date) VALUES (?, ?, ?, ?, ?)",
                    (float(amount), trans_type, category, txn_currency, txn_date.strftime("%Y-%m-%d"))
                )
                conn.commit()
                conn.close()
                st.success(f"Added {trans_type} of {LABEL_TO_SYMBOL[txn_currency]}{amount:.2f} ({txn_currency})")

# ------------------ DASHBOARD ------------------ #
elif menu == "📊 Dashboard":
    st.title("📊 Finance Dashboard")
    st.markdown(f"Showing amounts converted to **{st.session_state.ui_currency}**")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("No transactions yet — add one in 'Add Transaction'.")
    else:
        # ensure date column is parsed
        df['date'] = pd.to_datetime(df['date'])
        # filter UI controls
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filters")
        # Date range filter defaults
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        dr = st.sidebar.date_input("Date range", value=(min_date, max_date))
        if isinstance(dr, tuple) and len(dr) == 2:
            start_date, end_date = dr
        else:
            start_date, end_date = min_date, max_date

        categories = sorted(df['category'].unique().tolist())
        sel_categories = st.sidebar.multiselect("Categories", options=categories, default=categories)
        sel_types = st.sidebar.multiselect("Type", options=["income", "expense"], default=["income", "expense"])

        # apply filters
        filtered = df[
            (df['date'].dt.date >= start_date) &
            (df['date'].dt.date <= end_date) &
            (df['category'].isin(sel_categories)) &
            (df['type'].isin(sel_types))
        ].copy()

        if filtered.empty:
            st.warning("No data matches the selected filters.")
        else:
            # Convert amounts to UI currency for display & aggregation
            ui_label = st.session_state.ui_currency
            filtered['converted_amount'] = filtered.apply(
                lambda r: convert_amount(r['amount'], r['currency'], ui_label), axis=1
            )

            # Summary metrics
            total_income = filtered.loc[filtered['type'] == 'income', 'converted_amount'].sum()
            total_expense = filtered.loc[filtered['type'] == 'expense', 'converted_amount'].sum()
            balance = total_income - total_expense
            symbol = LABEL_TO_SYMBOL.get(ui_label, ui_label.split()[1] if len(ui_label.split())>1 else "")

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Income", f"{symbol}{total_income:,.2f}")
            c2.metric("Total Expense", f"{symbol}{total_expense:,.2f}")
            c3.metric("Balance", f"{symbol}{balance:,.2f}")

            if total_expense > total_income:
                st.error("⚠️ Expenses exceed income for the selected filters.")

            st.markdown("---")
            # Charts area
            left, right = st.columns([2, 1])

            # left: expense breakdown pie
            with left:
                expense_df = filtered[filtered['type'] == 'expense']
                if not expense_df.empty:
                    # aggregate by category (sum converted_amount)
                    by_cat = expense_df.groupby('category', as_index=False)['converted_amount'].sum()
                    fig = px.pie(by_cat, names='category', values='converted_amount',
                                 title=f"Expenses by Category ({ui_label})", hole=0.3)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No expense data for selected filters.")

                # monthly bar chart
                filtered['month'] = filtered['date'].dt.strftime('%Y-%m')
                monthly = filtered.groupby(['month','type'], as_index=False)['converted_amount'].sum()
                if not monthly.empty:
                    # ensure months are sorted chronologically
                    monthly = monthly.sort_values('month')
                    fig2 = px.bar(monthly, x='month', y='converted_amount', color='type',
                                  title=f"Monthly Income vs Expense ({ui_label})", barmode='group')
                    fig2.update_layout(xaxis_title="Month", yaxis_title=f"Amount ({ui_label})")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No monthly data to show.")

            # right: top categories and conversion note
            with right:
                st.subheader("Top Expense Categories")
                if not expense_df.empty:
                    top = expense_df.groupby('category', as_index=False)['converted_amount'].sum().sort_values('converted_amount', ascending=False).head(5)
                    top['formatted'] = top['converted_amount'].apply(lambda x: f"{symbol}{x:,.2f}")
                    st.table(top[['category','formatted']].rename(columns={'category':'Category','formatted':'Amount'}))
                else:
                    st.write("No expenses.")

                st.markdown("---")
                if not FOREX_AVAILABLE:
                    st.warning("Currency conversion not available (forex-python missing). Showing raw amounts for same-currency transactions only.")
                else:
                    st.caption("Conversion rates cached for an hour. Minor rounding applied.")

# ------------------ TRANSACTIONS PAGE ------------------ #
elif menu == "📜 Transactions":
    st.title("📜 Transaction History (Filtered & Exportable)")
    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df_all.empty:
        st.info("No transactions yet.")
    else:
        # filters specifically for transactions page
        df_all['date'] = pd.to_datetime(df_all['date'])
        min_date = df_all['date'].dt.date.min()
        max_date = df_all['date'].dt.date.max()

        colA, colB, colC = st.columns([2,2,1])
        with colA:
            dr = st.date_input("Date range", value=(min_date, max_date))
            if isinstance(dr, tuple) and len(dr)==2:
                s_date, e_date = dr
            else:
                s_date, e_date = min_date, max_date
        with colB:
            category_filter = st.multiselect("Category", sorted(df_all['category'].unique()), default=sorted(df_all['category'].unique()))
        with colC:
            txn_type_filter = st.multiselect("Type", ["income", "expense"], default=["income","expense"])

        view_currency = st.selectbox("View CSV amounts in:", LABELS, index=LABELS.index(st.session_state.ui_currency))

        # apply filters
        df_view = df_all[
            (df_all['date'].dt.date >= s_date) &
            (df_all['date'].dt.date <= e_date) &
            (df_all['category'].isin(category_filter)) &
            (df_all['type'].isin(txn_type_filter))
        ].copy()

        if df_view.empty:
            st.warning("No transactions match filters.")
        else:
            # convert amounts to selected view_currency for CSV/download and display
            df_view['converted_amount'] = df_view.apply(lambda r: convert_amount(r['amount'], r['currency'], view_currency), axis=1)
            symbol = LABEL_TO_SYMBOL.get(view_currency, "")

            display_df = df_view[['id','date','type','category','currency','amount','converted_amount']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df = display_df.rename(columns={
                'id':'ID','type':'Type','category':'Category','currency':'Original Currency',
                'amount':'Original Amount', 'converted_amount':f'Amount ({view_currency})'
            })
            st.dataframe(display_df, use_container_width=True)

            # CSV download (filtered)
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download CSV ({view_currency})",
                data=csv,
                file_name=f"transactions_{view_currency.replace(' ','_')}.csv",
                mime='text/csv'
            )
