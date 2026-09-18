import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import html as html_lib
from datetime import datetime

st.set_page_config(
    page_title="Random People Picker",
    page_icon="🎰",
    layout="centered"
)

# =====================================================
# CONFIG
# =====================================================

try:
    SPIN_PASSWORD = st.secrets["SPIN_PASSWORD"]   # only works if a secrets.toml exists
except Exception:
    SPIN_PASSWORD = "nothing"                        # fallback when no secrets file is set up

REQUIRED_COLS = ["Name", "Department", "Email", "Selected"]
DB_PATH = "people.xlsx"

# =====================================================
# THEME / GLOBAL STYLES
# =====================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 50% 0%, #241a4a 0%, #150e2b 55%, #0f0a20 100%);
    color: #F3EEDD;
}

h1, h2, h3 {
    font-family: 'Baloo 2', sans-serif;
    color: #F7D774;
}

section[data-testid="stSidebar"] {
    background: #17112f;
    border-right: 1px solid #3a2d66;
}
section[data-testid="stSidebar"] * {
    color: #EDE7FF;
}

.stat-strip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 28px;
    padding: 14px 0 20px 0;
    margin-bottom: 6px;
}
.stat {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.stat-value {
    font-family: 'Baloo 2', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: #F7D774;
    line-height: 1.1;
}
.stat-label {
    font-size: 13px;
    color: #B8AEDC;
    margin-top: 2px;
}
.stat-divider {
    width: 1px;
    height: 34px;
    background: #3a2d66;
}

.stButton > button {
    font-family: 'Baloo 2', sans-serif;
    font-weight: 600;
    font-size: 18px;
    letter-spacing: 0.3px;
    color: #1a1030;
    background: linear-gradient(135deg, #FBD976, #F0A63B);
    border: none;
    border-radius: 14px;
    padding: 10px 0;
    box-shadow: 0 6px 0 #a5701c, 0 10px 18px rgba(0,0,0,0.35);
    transition: transform 0.08s ease;
}
.stButton > button:hover { transform: translateY(-2px); }
.stButton > button:active {
    transform: translateY(2px);
    box-shadow: 0 3px 0 #a5701c, 0 6px 12px rgba(0,0,0,0.35);
}

.winner-card {
    margin: 18px 0 6px 0;
    padding: 22px 18px;
    border-radius: 18px;
    text-align: center;
    background: linear-gradient(160deg, #2a1f55, #1c1440);
    border: 1px solid #F7D774;
    box-shadow: 0 0 0 1px rgba(247,215,116,0.15), 0 14px 30px rgba(0,0,0,0.4);
    animation: pop-in 0.5s cubic-bezier(.26,1.6,.5,1);
}
@keyframes pop-in {
    0% { transform: scale(0.85); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}
.winner-label { font-size: 14px; color: #B8AEDC; margin-bottom: 6px; }
.winner-name {
    font-family: 'Baloo 2', sans-serif;
    font-size: 34px;
    font-weight: 700;
    color: #F7D774;
    text-shadow: 0 2px 12px rgba(247,215,116,0.4);
}
.winner-chips {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-top: 16px;
}
.chip {
    background: #241a4a;
    border: 1px solid #3a2d66;
    border-radius: 12px;
    padding: 8px 14px;
    min-width: 150px;
}
.chip-name { font-family: 'Baloo 2', sans-serif; font-weight: 600; color: #F3EEDD; font-size: 16px; }
.chip-dept {
    display: inline-block;
    font-size: 11px;
    color: #1a1030;
    background: #9DE0C8;
    border-radius: 8px;
    padding: 1px 8px;
    margin-top: 4px;
}
.chip-email { font-size: 12px; color: #B8AEDC; margin-top: 3px; }

.history-item {
    padding: 12px 14px;
    border-radius: 12px;
    background: #1c1440;
    margin-bottom: 8px;
    border-left: 4px solid #F7D774;
}
.history-item b { color: #F3EEDD; }
.history-meta { color: #B8AEDC; font-size: 12px; margin-top: 2px; }

[data-testid="stFileUploader"], [data-testid="stTextInput"] input { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# SLOT REEL COMPONENT  (replaces the old spin wheel)
# =====================================================

def render_reel(names, winner_name=None):
    """
    A vertical slot-machine style reel. Scales cleanly from 5 names to
    500+ names — unlike a pie wheel, nothing gets cramped or unreadable.
    """
    if not names:
        st.info("No people loaded yet — import an Excel file from the sidebar.")
        return

    names_json = json.dumps(names)
    winner_json = json.dumps(winner_name) if winner_name else json.dumps("")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
    <style>
        body {{
            margin: 0;
            font-family: 'Inter', Arial, sans-serif;
            text-align: center;
            background: transparent;
        }}
        .stage {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 10px;
        }}
        .reel-shell {{
            position: relative;
            width: 340px;
        }}
        .reel-viewport {{
            position: relative;
            width: 100%;
            height: 280px;
            overflow: hidden;
            border-radius: 18px;
            background: #1c1440;
            border: 1px solid #3a2d66;
            box-shadow: inset 0 0 30px rgba(0,0,0,0.55), 0 12px 28px rgba(0,0,0,0.4);
        }}
        .reel-track {{
            position: absolute;
            left: 0; right: 0; top: 0;
            will-change: transform;
        }}
        .reel-item {{
            height: 56px;
            line-height: 56px;
            font-family: 'Baloo 2', 'Inter', sans-serif;
            font-size: 20px;
            font-weight: 600;
            color: #C9C2E8;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 16px;
        }}
        .fade {{
            position: absolute;
            left: 0; right: 0;
            height: 90px;
            pointer-events: none;
            z-index: 3;
        }}
        .fade-top    {{ top: 0;    background: linear-gradient(#1c1440, rgba(28,20,64,0)); }}
        .fade-bottom {{ bottom: 0; background: linear-gradient(rgba(28,20,64,0), #1c1440); }}
        .center-window {{
            position: absolute;
            left: 6px; right: 6px;
            top: 112px;
            height: 56px;
            border-radius: 10px;
            border: 2px solid #F7D774;
            box-shadow: 0 0 0 3px rgba(247,215,116,0.12);
            pointer-events: none;
            z-index: 2;
            transition: box-shadow 0.3s ease;
        }}
        .center-window.landed {{
            box-shadow: 0 0 24px 4px rgba(247,215,116,0.55);
        }}
        .marker {{
            width: 0; height: 0;
            border-top: 9px solid transparent;
            border-bottom: 9px solid transparent;
            position: absolute;
            top: 132px;
            z-index: 4;
        }}
        .marker-left  {{ left: -4px;  border-left: 11px solid #F7D774; }}
        .marker-right {{ right: -4px; border-right: 11px solid #F7D774; }}
        .caption {{
            margin-top: 16px;
            font-size: 15px;
            color: #B8AEDC;
            min-height: 20px;
        }}
    </style>
    </head>
    <body>
    <div class="stage">
        <div class="reel-shell">
            <div class="marker marker-left"></div>
            <div class="marker marker-right"></div>
            <div class="reel-viewport">
                <div id="reelTrack" class="reel-track"></div>
                <div class="fade fade-top"></div>
                <div class="fade fade-bottom"></div>
            </div>
            <div id="centerWindow" class="center-window"></div>
        </div>
        <div class="caption" id="caption">{len(names)} people loaded — press SPIN</div>
    </div>

    <script>
    const names = {names_json};
    const winner = {winner_json};

    const ITEM_H = 56;
    const VISIBLE_ROWS = 5;
    const CENTER_ROW = 2; // 0-indexed, middle of 5 visible rows

    const track = document.getElementById("reelTrack");
    const centerWindow = document.getElementById("centerWindow");
    const caption = document.getElementById("caption");

    function itemHTML(name) {{
        const div = document.createElement("div");
        div.className = "reel-item";
        div.textContent = name;
        return div;
    }}

    function renderStatic(list) {{
        track.innerHTML = "";
        list.forEach(n => track.appendChild(itemHTML(n)));
    }}

    if (!winner) {{
        // idle state: just show the names, centered, no animation
        const filler = names.slice(0, Math.max(names.length, VISIBLE_ROWS));
        renderStatic(filler);
        track.style.transform = "translateY(" + (CENTER_ROW * ITEM_H) + "px)";
    }} else {{
        // build a long shuffled reel that ends exactly on the winner
        const targetLen = Math.min(Math.max(names.length * 4, 60), 220);
        let reel = [];
        while (reel.length < targetLen) {{
            let batch = names.slice();
            for (let i = batch.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1));
                [batch[i], batch[j]] = [batch[j], batch[i]];
            }}
            reel.push(...batch);
        }}
        reel.push(winner);
        const winnerIndex = reel.length - 1;

        renderStatic(reel);

        const finalY = (CENTER_ROW - winnerIndex) * ITEM_H;
        let startTime = null;
        const duration = 4600;

        function animate(time) {{
            if (!startTime) startTime = time;
            const elapsed = time - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 4);
            const y = finalY * ease;
            track.style.transform = "translateY(" + y + "px)";

            if (progress < 1) {{
                requestAnimationFrame(animate);
            }} else {{
                centerWindow.classList.add("landed");
                caption.textContent = "🏆 " + winner;
                if (window.confetti) {{
                    confetti({{ particleCount: 220, spread: 110, origin: {{ y: 0.6 }} }});
                    setTimeout(() => confetti({{ particleCount: 120, spread: 140, origin: {{ y: 0.5 }} }}), 250);
                }}
            }}
        }}
        requestAnimationFrame(animate);
    }}
    </script>
    </body>
    </html>
    """

    components.html(html, height=400)

# =====================================================
# AUTH
# =====================================================

st.sidebar.subheader("🔐 Authorization")

picked_by = st.sidebar.text_input("Your name", placeholder="Enter your name")
password = st.sidebar.text_input("Spin password", type="password")

is_authorized = password == SPIN_PASSWORD

if password:
    if is_authorized:
        st.sidebar.success("Authorized ✅")
    else:
        st.sidebar.error("Wrong password ❌")
else:
    st.sidebar.info("View-only mode — enter the password to spin")

# =====================================================
# IMPORT FILE
# =====================================================

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Import Excel file")

uploaded = st.sidebar.file_uploader("Choose an .xlsx file", type=["xlsx"])

if uploaded is not None:
    if st.sidebar.button("Use this file as DB"):
        with open(DB_PATH, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.last_pick = None
        st.session_state.winner_name = None
        st.sidebar.success(f"Imported {uploaded.name}")
        st.rerun()

# =====================================================
# DATABASE FUNCTIONS
# =====================================================

def save_db(path, people, history):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        people.to_excel(writer, sheet_name="People", index=False)
        history.to_excel(writer, sheet_name="History", index=False)

def load_db(path):
    if not os.path.exists(path):
        people = pd.DataFrame({
            "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "Department": ["Engineering", "Sales", "Engineering", "HR", "Marketing"],
            "Email": ["alice@example.com", "bob@example.com", "charlie@example.com",
                      "diana@example.com", "eve@example.com"],
            "Selected": [False] * 5
        })
        history = pd.DataFrame(columns=["Timestamp", "Cycle", "Names", "PickedBy"])
        save_db(path, people, history)
        return people, history

    sheets = pd.read_excel(path, sheet_name=None)
    people = sheets.get("People", list(sheets.values())[0])
    history = sheets.get("History", pd.DataFrame(columns=["Timestamp", "Cycle", "Names", "PickedBy"]))

    for col in REQUIRED_COLS:
        if col not in people.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    people["Selected"] = people["Selected"].fillna(False).astype(bool)
    # never let stray HTML/formulas in imported data break our markup later
    for col in ["Name", "Department", "Email"]:
        people[col] = people[col].astype(str)

    return people, history

# =====================================================
# LOAD DATA + STATE
# =====================================================

people, history = load_db(DB_PATH)

if "last_pick" not in st.session_state:
    st.session_state.last_pick = None
if "winner_name" not in st.session_state:
    st.session_state.winner_name = None
if "show_balloons" not in st.session_state:
    st.session_state.show_balloons = False

# =====================================================
# CALCULATIONS
# =====================================================

total = len(people)
remaining = int((~people["Selected"]).sum())

if history.empty or "Cycle" not in history.columns or history["Cycle"].dropna().empty:
    cycle_no = 1
else:
    cycle_no = int(history["Cycle"].max())

# =====================================================
# HEADER + STATS
# =====================================================

st.markdown("<h1 style='text-align:center;'>🎰 Random People Picker</h1>", unsafe_allow_html=True)

st.markdown(f"""
<div class="stat-strip">
    <div class="stat"><span class="stat-value">{total}</span><span class="stat-label">Total people</span></div>
    <div class="stat-divider"></div>
    <div class="stat"><span class="stat-value">{remaining}</span><span class="stat-label">Remaining</span></div>
    <div class="stat-divider"></div>
    <div class="stat"><span class="stat-value">{cycle_no}</span><span class="stat-label">Cycle</span></div>
</div>
""", unsafe_allow_html=True)

render_reel(people["Name"].tolist(), st.session_state.winner_name)

n = st.radio("How many people to pick?", [1, 3], horizontal=True)

# =====================================================
# SPIN
# =====================================================

if is_authorized:
    if st.button("🎯  SPIN", type="primary", use_container_width=True):
        pool = people[~people["Selected"]]
        new_cycle = False

        if len(pool) == 0:
            people["Selected"] = False
            pool = people.copy()
            cycle_no += 1
            new_cycle = True

        pick_n = min(n, len(pool))
        chosen = pool.sample(n=pick_n)
        people.loc[chosen.index, "Selected"] = True

        picked_names = ", ".join(chosen["Name"].tolist())

        log_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Cycle": cycle_no,
            "Names": picked_names,
            "PickedBy": picked_by.strip() if picked_by.strip() else "Unknown"
        }])
        history = pd.concat([history, log_row], ignore_index=True)

        save_db(DB_PATH, people, history)

        st.session_state.winner_name = chosen.iloc[0]["Name"]
        st.session_state.last_pick = {
            "names": chosen[["Name", "Department", "Email"]],
            "new_cycle": new_cycle
        }
        st.session_state.show_balloons = True
        st.rerun()
else:
    st.warning("🔒 Enter the correct password in the sidebar to spin.")

# =====================================================
# RESULT
# =====================================================

if st.session_state.last_pick is not None:
    result = st.session_state.last_pick

    if st.session_state.show_balloons:
        st.balloons()
        st.session_state.show_balloons = False

    if result["new_cycle"]:
        st.info("Everyone had already been picked — a new cycle just started.")

    # Built as flat, single-line HTML with no indentation and no blank
    # lines: Markdown treats indented lines after a blank line as a code
    # block (that's why chips used to render as raw text with a "copy"
    # button instead of styled HTML), so we avoid giving it that chance.
    chip_parts = []
    for _, row in result["names"].iterrows():
        chip_parts.append(
            '<div class="chip">'
            f'<div class="chip-name">{html_lib.escape(str(row["Name"]))}</div>'
            f'<div class="chip-dept">{html_lib.escape(str(row["Department"]))}</div>'
            f'<div class="chip-email">{html_lib.escape(str(row["Email"]))}</div>'
            '</div>'
        )
    chips_html = "".join(chip_parts)

    winner_names_display = html_lib.escape(", ".join(result["names"]["Name"].tolist()))

    winner_card_html = (
        '<div class="winner-card">'
        '<div class="winner-label">This spin\'s pick</div>'
        f'<div class="winner-name">🏆 {winner_names_display}</div>'
        f'<div class="winner-chips">{chips_html}</div>'
        '</div>'
    )
    st.markdown(winner_card_html, unsafe_allow_html=True)

    with st.expander("View as table"):
        st.dataframe(result["names"], use_container_width=True)

# =====================================================
# HISTORY
# =====================================================

st.subheader("📜 Spin history")

if history.empty:
    st.info("No spin history yet.")
else:
    history_view = history.sort_values("Timestamp", ascending=False)
    for _, row in history_view.iterrows():
        st.markdown(f"""
        <div class="history-item">
            <b>{html_lib.escape(str(row['Names']))}</b>
            <div class="history-meta">Cycle {html_lib.escape(str(row['Cycle']))} &nbsp;|&nbsp; Picked by {html_lib.escape(str(row['PickedBy']))} &nbsp;|&nbsp; {html_lib.escape(str(row['Timestamp']))}</div>
        </div>
        """, unsafe_allow_html=True)

st.subheader("👥 People")
st.dataframe(people, use_container_width=True)
