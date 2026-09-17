# Random People Picker

Streamlit app that randomly picks 1 or 3 people from an Excel sheet, without
repeating anyone until everyone has been picked once (a "cycle").

## Files
- `app.py` — the Streamlit app
- `requirements.txt` — Python dependencies
- `people.xlsx` — created automatically on first run if not present

## Steps to run

1. Unzip this folder and open a terminal inside it.

2. (Recommended) Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the app:
   ```
   streamlit run app.py
   ```

5. Your browser will open at `http://localhost:8501`.

6. On first run, if `people.xlsx` doesn't exist in this folder, the app
   creates a sample one automatically with columns:
   `Name, Department, Email, Selected`.
   Replace the sample rows with your real list — keep these column names.
   You can add extra columns (e.g. phone, role); they'll be preserved but
   unused by the app.

7. In the app:
   - Choose 1 or 3 as the number of people to pick.
   - Click **Spin** — it picks randomly from people not yet selected this
     cycle and marks them `Selected = True` in the Excel file.
   - Once everyone has been picked, the next spin auto-resets the cycle
     (`Selected` reset to `False` for all) and picks from the full list
     again.
   - Check the **Spin history** section for a log of every spin
     (timestamp, cycle number, names picked).

## Notes
- Close `people.xlsx` in Excel before spinning — the app can't save to it
  while it's open elsewhere.
- Single-user/local use only; no concurrent-access locking.
