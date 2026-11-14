"""Sukkur Load Shedding Predictor - Streamlit dashboard.

Run with:   streamlit run app.py

What the user does: select an area, select a date, click Predict.
"""

from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import logic
from model import LoadSheddingModel

BASE_DIR = Path(__file__).parent
DEFAULT_AREA = "Ghanta Ghar (Clock Tower)"      # shown when the user selects nothing
GREEN, RED, BLUE = "#2da44e", "#cf222e", "#1f6feb"
CHANCE_LIMIT = 50        # below this chance, load shedding is "unlikely"
HIGH_CHANCE = 70         # weekly graph: red bar from this chance upwards

st.set_page_config(page_title="Sukkur Load Shedding Predictor", page_icon="⚡", layout="wide")

# Small CSS: only for the colours of the status boxes
st.markdown(
    """
    <style>
    .status-box {border-radius: 14px; padding: 22px 14px; text-align: center;
                 color: #ffffff; font-weight: 700; font-size: 1.7rem;}
    .status-box small {display: block; font-weight: 500; font-size: 0.9rem;
                       margin-top: 6px; opacity: 0.95;}
    .status-box.on {background: #2da44e;}
    .status-box.off {background: #cf222e;}
    .status-box.info {background: #1f6feb;}
    .count-box {border: 2px solid #d0d7de; border-radius: 14px; padding: 22px 14px;
                text-align: center; background: #f6f8fa;}
    .count-box .label {font-size: 0.95rem; color: #57606a;}
    .count-box .time {font-size: 2rem; font-weight: 700; color: #1b1f24;}
    @media (max-width: 640px) {h1 {font-size: 1.6rem !important;}
                               .status-box {font-size: 1.4rem;} .count-box .time {font-size: 1.6rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- data + model
@st.cache_data
def load_timings():
    return pd.read_csv(BASE_DIR / "data" / "area_timings.csv", dtype=str)


@st.cache_resource
def load_model():
    model = LoadSheddingModel()
    model.train()
    return model


timings = load_timings()
model = load_model()
areas = timings["Area"].tolist()


def timing_of(area):
    row = timings.loc[timings["Area"] == area].iloc[0]
    return row["Light Off Time"], row["Light On Time"]


# ---------------------------------------------------------------- html helpers
def status_box(kind, title, note):
    return f'<div class="status-box {kind}">{title}<small>{note}</small></div>'


def count_box(label, value):
    return f'<div class="count-box"><div class="label">{label}</div><div class="time">{value}</div></div>'


# ---------------------------------------------------------------- live part
def render_live(off, on, likely, chance, is_today, day_text, next_chance):
    """Status box + countdown. For today this block refreshes every second."""
    left, right = st.columns(2)

    if not likely:
        left.markdown(
            status_box("on", "💡 LIGHT IS ON", f"Load shedding is unlikely on {day_text} (chance {chance:.0f}%)"),
            unsafe_allow_html=True,
        )
        right.markdown(count_box("Countdown", "No outage expected"), unsafe_allow_html=True)
        return

    if not is_today:
        left.markdown(
            status_box("info", "📅 FORECAST", f"For {day_text}"), unsafe_allow_html=True
        )
        right.markdown(
            count_box("Expected outage", f"{logic.fmt_12h(off)} – {logic.fmt_12h(on)}"),
            unsafe_allow_html=True,
        )
        return

    now = logic.now_pk()
    state, seconds_left = logic.live_state(logic.seconds_since_midnight(now), off, on)
    note = "Expected status from the predicted schedule"
    if state == "DURING":
        left.markdown(status_box("off", "🔴 LIGHT IS OFF", note), unsafe_allow_html=True)
        right.markdown(count_box("Light will come back in", logic.fmt_countdown(seconds_left)),
                       unsafe_allow_html=True)
    elif state == "BEFORE":
        left.markdown(status_box("on", "🟢 LIGHT IS ON", note), unsafe_allow_html=True)
        right.markdown(count_box("Light will go off in", logic.fmt_countdown(seconds_left)),
                       unsafe_allow_html=True)
    else:
        left.markdown(status_box("on", "🟢 LIGHT IS ON", "Today's outage is over"), unsafe_allow_html=True)
        if next_chance >= CHANCE_LIMIT:
            right.markdown(count_box("Tomorrow's outage starts in", logic.fmt_countdown(seconds_left)),
                           unsafe_allow_html=True)
        else:
            right.markdown(count_box("Tomorrow", "Load shedding unlikely"), unsafe_allow_html=True)
    st.caption(f"Pakistan time now: {now:%I:%M:%S %p}")


# ---------------------------------------------------------------- graphs
def pie_chart(off_minutes):
    off_hours = off_minutes / 60
    fig = go.Figure(go.Pie(
        labels=["Light ON", "Light OFF"],
        values=[24 - off_hours, off_hours],
        marker=dict(colors=[GREEN, RED]),
        hole=0.45,
        texttemplate="%{label}<br>%{value:.1f} h",
        textposition="outside",
        sort=False,
    ))
    fig.update_layout(title="Hours ON vs OFF (one day)", height=340, showlegend=False,
                      margin=dict(l=10, r=10, t=90, b=30), template="plotly_white")
    return fig


def hours_label(hours):
    """10.5 -> '10:30 AM'  (24 -> '12:00 AM')."""
    minutes = round(hours * 60) % 1440
    return logic.fmt_12h(f"{minutes // 60:02d}:{minutes % 60:02d}")


def timeline_chart(off, on):
    off_h = logic.to_minutes(off) / 60
    on_h = logic.to_minutes(on) / 60
    segments = [(0, off_h, "ON", GREEN), (off_h, on_h, "OFF", RED), (on_h, 24, "ON", GREEN)]
    fig = go.Figure()
    shown = set()
    for start, end, state, color in segments:
        if end <= start:
            continue
        fig.add_trace(go.Bar(
            x=[end - start], y=["Today"], base=[start], orientation="h",
            marker_color=color, name=f"Light {state}", legendgroup=state,
            showlegend=state not in shown,
            hovertemplate=f"Light {state}<br>{hours_label(start)} to {hours_label(end)}<extra></extra>",
        ))
        shown.add(state)
    fig.update_layout(
        title="Full-day timeline (12 AM to 12 AM)", barmode="overlay", height=320,
        xaxis=dict(range=[0, 24], tickvals=list(range(0, 25, 3)),
                   ticktext=["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM", "12 AM"]),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=40, r=40, t=50, b=10), template="plotly_white",
    )
    return fig


def weekly_chart(area, start_day):
    days = [start_day + timedelta(days=i) for i in range(7)]
    chances = [model.chance(area, d) for d in days]
    colors = [RED if c >= HIGH_CHANCE else BLUE for c in chances]
    fig = go.Figure(go.Bar(
        x=[f"{d:%a}<br>{d:%d %b}" for d in days], y=chances,
        marker_color=colors, text=[f"{c:.0f}%" for c in chances], textposition="outside",
        hovertemplate="%{x}<br>Chance: %{y:.0f}%<extra></extra>",
    ))
    fig.add_hline(y=CHANCE_LIMIT, line_dash="dash", line_color="gray")
    fig.update_layout(title="Next 7 days: chance of load shedding", height=340,
                      yaxis=dict(range=[0, 115], title="Chance (%)"),
                      margin=dict(l=10, r=10, t=50, b=10), template="plotly_white")
    return fig


# ---------------------------------------------------------------- page
today = logic.now_pk().date()
if "sel_area" not in st.session_state:
    st.session_state.sel_area = DEFAULT_AREA
    st.session_state.sel_date = today

st.title("⚡ SUKKUR LOAD SHEDDING PREDICTOR")
st.caption("AI-based area estimate for Sukkur city  •  sample timings and sample data for a university project")

# Row 1: area + date + Predict
with st.form("predict_form"):
    c_area, c_date, c_btn = st.columns([3, 2, 1])
    picked_area = c_area.selectbox("Select area", areas, index=areas.index(st.session_state.sel_area))
    picked_date = c_date.date_input("Select date", value=st.session_state.sel_date)
    c_btn.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
    submitted = c_btn.form_submit_button("Predict", type="primary")
if submitted:
    st.session_state.sel_area = picked_area
    st.session_state.sel_date = picked_date or today

area = st.session_state.sel_area
day = st.session_state.sel_date
off, on = timing_of(area)
duration = logic.duration_minutes(off, on)
chance = model.chance(area, day)
likely = chance >= CHANCE_LIMIT
is_today = day == today
day_text = f"{day:%A, %d %B %Y}"

st.subheader(f"{area}  •  {day_text}")

# Row 2: live status + countdown (refreshes every second when the date is today)
next_day = day + timedelta(days=1)
next_chance = model.chance(area, next_day)

live = st.fragment(run_every=1 if is_today else None)(render_live)
live(off, on, likely, chance, is_today, day_text, next_chance)

# Summary numbers
m1, m2, m3, m4 = st.columns(4)
m1.metric("Light will go off", logic.fmt_12h(off))
m2.metric("Light will come back", logic.fmt_12h(on))
m3.metric("Total off duration", logic.fmt_duration(duration))
m4.metric("Chance of load shedding", f"{chance:.0f}%")
if not likely:
    st.info("The chance is below 50%, so load shedding is unlikely on this date. "
            "The times above are the normal timing if it does happen.")

# Row 3: pie chart + timeline graph
g1, g2 = st.columns([2, 3])
g1.plotly_chart(pie_chart(duration))
g2.plotly_chart(timeline_chart(off, on))

# Row 4: weekly graph
st.plotly_chart(weekly_chart(area, day))
st.caption("Blue bar = normal chance, red bar = high chance (70% or more). "
           "Dashed line = 50% (below it, load shedding is unlikely).")

# Row 5: tomorrow's prediction
st.subheader("Tomorrow's prediction" if is_today else f"Next day's prediction ({next_day:%a, %d %b})")
if next_chance >= CHANCE_LIMIT:
    st.warning(f"Light will go off at **{logic.fmt_12h(off)}** and come back at "
               f"**{logic.fmt_12h(on)}**  (chance {next_chance:.0f}%)")
else:
    st.success(f"Load shedding is unlikely (chance {next_chance:.0f}%).")

# Sidebar: about + model info + honest notes
with st.sidebar:
    st.header("About")
    st.write("Select an area and a date, then click **Predict**. "
             "No typing of data is needed.")
    st.subheader("Machine Learning model")
    st.write("Random Forest Classifier")
    st.write(f"Training rows: **{model.rows:,}**")
    st.write(f"Test accuracy: **{model.accuracy * 100:.0f}%**")
    st.caption("Inputs: area, weekday, temperature. "
               "Accuracy is measured on SAMPLE data, so it is not real-world accuracy.")
    st.subheader("Please note")
    st.caption("• Timings and history are sample data made for a university project.\n\n"
               "• This is an area-based estimate, not an official SEPCO feeder schedule.\n\n"
               "• Light status is the expected status from the predicted schedule, "
               "not a live sensor.")
    st.divider()
    st.caption("Developed by Ali Nawaz  \nDawood University of Engineering & Technology (DUET), Karachi  \n"
               "Subject: Technical Report Writing")
