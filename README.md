# FinTrack

**Take control of your money, one transaction at a time.**

FinTrack is a full-stack web application that helps users track, categorize, and visualize their personal income and expenses. It provides a simple and intuitive interface to manage finances and gain insights into spending habits.

---

## Features
- Add income and expense transactions
- Categorize transactions for better clarity
- View transactions in a clean list
- Visualize financial data using interactive charts (via Streamlit frontend)
- Robust backend with Flask and SQLite

---

## Tech Stack
- **Backend:** Flask, SQLite
- **Frontend:** Streamlit
- **Other:** Flask-CORS, Requests
- **Deployment:** Streamlit Cloud / Heroku

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/FinTrack.git
cd FinTrack
```
2. Create a virtual environment and activate it:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4.Run the backend Flask server:
```bash
python app.py
```
5. Run the Streamlit frontend:
```bash
streamlit run streamlit_app.py
```
---

## Usage
1. Open the Streamlit app in your browser.
2. Add transactions using the form (amount, type, category).
3. View your transactions and track your finances.
4. (Optional) Visualize trends and summaries using charts.
---

## Folder Structure
```
FinTrack/
│
├─ app.py                 # Flask backend
├─ streamlit_app.py       # Streamlit frontend
├─ requirements.txt       # Python dependencies
├─ Procfile               # Deployment instructions
├─ runtime.txt            # Python version
├─ finance.db             # SQLite database
├─ .gitignore             # Ignored files
└─ README.md              # Project documentation
```
---

## Contributing
- Contributions are welcome! Feel free to open issues or submit pull requests to improve FinTrack.
---

## License
- This project is open-source and free to use under the MIT License.
---

## Author

