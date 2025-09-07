from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, 'finance.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create transactions table if it doesn't exist."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize DB
with app.app_context():
    init_db()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """Add a new transaction."""
    data = request.get_json()
    
    # Validation
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if 'amount' not in data or not isinstance(data['amount'], (int, float)):
        return jsonify({"error": "Amount is required and must be a number"}), 400
    if 'type' not in data or data['type'] not in ('income', 'expense'):
        return jsonify({"error": "Type must be 'income' or 'expense'"}), 400
    
    amount = data['amount']
    trans_type = data['type']
    category = data.get('category', 'Uncategorized')
    date = data.get('date', datetime.now().strftime("%Y-%m-%d"))

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO transactions (amount, type, category, date) VALUES (?, ?, ?, ?)",
            (amount, trans_type, category, date)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Transaction added successfully"}), 201
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Retrieve all transactions."""
    conn = get_db_connection()
    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC"
    ).fetchall()
    conn.close()
    
    transactions_list = [dict(row) for row in transactions]
    return jsonify(transactions_list), 200

if __name__ == "__main__":
    app.run(debug=True)
