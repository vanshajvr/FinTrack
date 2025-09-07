from flask import Flask, jsonify, request
from flask_cors import CORS # Import the CORS extension
import sqlite3
import os

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the path to the SQLite database file
DATABASE_FILE = os.path.join(BASE_DIR, 'finance.db')

def get_db_connection():
    """Establishes and returns a new connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def init_db():
    """Initializes the database by creating the transactions table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database when the app starts
with app.app_context():
    init_db()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """Adds a new transaction to the database."""
    data = request.get_json()
    if not data or 'amount' not in data or 'type' not in data:
        return jsonify({"error": "Missing data"}), 400

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO transactions (amount, type, category, date) VALUES (?, ?, ?, ?)",
            (data['amount'], data['type'], data.get('category', 'Uncategorized'), data.get('date', ''))
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"message": "Transaction added successfully"}), 201

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Retrieves all transactions from the database."""
    conn = get_db_connection()
    transactions = conn.execute("SELECT * FROM transactions ORDER BY date DESC").fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    transactions_list = [dict(row) for row in transactions]
    return jsonify(transactions_list), 200

if __name__ == '__main__':
    # To run this, you need to install Flask and Flask-CORS: pip install Flask Flask-CORS
    app.run(debug=True)
