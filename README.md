# FinTrack 💰

**Take control of your money, one transaction at a time.**  

FinTrack is a **pure Streamlit app** for tracking personal income and expenses. Add transactions, categorize them, and visualize your finances—all in one interactive dashboard. Fully deployable on **Streamlit Cloud** for free.

---

## Features
- Add income and expense transactions
- Categorize transactions
- View all transactions in a clean list
- Summary of total income, expenses, and balance
- Built entirely in Streamlit with SQLite database

---

## Tech Stack
- **Frontend & Backend:** Streamlit
- **Database:** SQLite
- **Deployment:** Streamlit Cloud (free)

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
2. Add income or expense transactions using the form.
3. View all transactions and track your finances.
4. Check your balance summary at a glance.
---

## Folder Structure
```
FinTrack/
├─ streamlit_app.py
├─ requirements.txt
├─ finance.db   # created automatically
└─ README.md
```
---

## Contributing
- Contributions are welcome! Feel free to open issues or submit pull requests to improve FinTrack.
---

## License
- MIT License
---

