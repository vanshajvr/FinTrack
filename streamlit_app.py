import streamlit as st
import requests

API_URL = "http://localhost:5000/api/transactions"  # Change to your deployed URL

st.title("Personal Finance Tracker")

# Form to add a transaction
with st.form("Add Transaction"):
    amount = st.number_input("Amount", min_value=0.0)
    type_ = st.selectbox("Type", ["income", "expense"])
    category = st.text_input("Category")
    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        data = {"amount": amount, "type": type_, "category": category}
        response = requests.post(API_URL, json=data)
        if response.status_code == 201:
            st.success("Transaction added!")
        else:
            st.error(f"Error: {response.json().get('error')}")

# Display transactions
if st.button("Load Transactions"):
    response = requests.get(API_URL)
    if response.status_code == 200:
        transactions = response.json()
        for t in transactions:
            st.write(f"{t['date']} - {t['type'].capitalize()} - {t['category']} - ₹{t['amount']}")
    else:
        st.error("Failed to load transactions.")
