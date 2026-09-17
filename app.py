import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Random People Picker", layout="centered")

REQUIRED_COLS = ["Name", "Department", "Email", "Selected"]

DB_PATH = st.sidebar.text_input("Excel DB path", value="people.xlsx")

st.sidebar.markdown("---")
st.sidebar.subheader("Import Excel file")
uploaded = st.sidebar.file_uploader("Choose an .xlsx from your computer", type=["xlsx"])
if uploaded is not None:
    if st.sidebar.button("Use this file as DB"):
        with open(DB_PATH, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.last_pick = None  # imported file, clear stale result
        st.sidebar.success(f"Imported '{uploaded.name}' → saved as '{DB_PATH}'")
        st.rerun()


def save_db(path, people, history):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        people.to_excel(writer, sheet_name="People", index=False)
        history.to_excel(writer, sheet_name="History", index=False)


def load_db(path):
    if not os.path.exists(path):
        st.sidebar.warning("DB not found. Created a sample one.")
        people = pd.DataFrame({
            "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "Department": ["Eng", "Sales", "Eng", "HR", "Marketing"],
            "Email": ["alice@x.com", "bob@x.com", "charlie@x.com", "diana@x.com", "eve@x.com"],
            "Selected": [False] * 5,
        })
        history = pd.DataFrame(columns=["Timestamp", "Cycle", "Names"])
        save_db(path, people, history)
        return people, history

    sheets = pd.read_excel(path, sheet_name=None)
    people = sheets.get("People", list(sheets.values())[0])
    history = sheets.get("History", pd.DataFrame(columns=["Timestamp", "Cycle", "Names"]))

    for col in REQUIRED_COLS:
        if col not in people.columns:
            st.error(f"'{DB_PATH}' is missing required column: {col}")
            st.stop()

    people["Selected"] = people["Selected"].fillna(False).astype(bool)
    return people, history


people, history = load_db(DB_PATH)

if "last_pick" not in st.session_state:
    st.session_state.last_pick = None

st.title("🎲 Random People Picker")

total = len(people)
remaining = int((~people["Selected"]).sum())
cycle_no = int(history["Cycle"].max()) if not history.empty else 1

c1, c2, c3 = st.columns(3)
c1.metric("Total people", total)
c2.metric("Remaining this cycle", remaining)
c3.metric("Current cycle", cycle_no)

st.dataframe(people, use_container_width=True)

n = st.radio("How many to pick?", [1, 3], horizontal=True)

if st.button("Spin 🎯", type="primary"):
    pool = people[~people["Selected"]]
    new_cycle = False

    if len(pool) == 0:
        # everyone already picked -> start a fresh cycle
        people["Selected"] = False
        pool = people.copy()
        new_cycle = True
        cycle_no += 1

    pick_n = min(n, len(pool))
    chosen = pool.sample(pick_n)

    people.loc[chosen.index, "Selected"] = True

    log_row = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Cycle": cycle_no,
        "Names": ", ".join(chosen["Name"].tolist()),
    }])
    history = pd.concat([history, log_row], ignore_index=True)

    save_db(DB_PATH, people, history)

    # persist the result in session_state so it stays visible across reruns
    st.session_state.last_pick = {
        "names": chosen[["Name", "Department", "Email"]],
        "new_cycle": new_cycle,
    }
    st.rerun()

# always show the most recent pick, if any, regardless of button state
if st.session_state.last_pick is not None:
    lp = st.session_state.last_pick
    st.markdown("### Last spin result")
    if lp["new_cycle"]:
        st.info("Everyone had already been picked — new cycle started.")
    st.success(f"Selected: {', '.join(lp['names']['Name'].tolist())}")
    st.dataframe(lp["names"], use_container_width=True)

with st.expander("Spin history"):
    st.dataframe(history.sort_values("Timestamp", ascending=False), use_container_width=True)
