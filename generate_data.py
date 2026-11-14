"""Creates the two data files of the project.

1. data/area_timings.csv : ONE fixed sample timing for each of the 32 areas.
2. data/history.csv      : one year of SAMPLE (simulated) history for the ML model.

IMPORTANT: all timings and all history here are SAMPLE data made for this
university project. They are not official SEPCO schedules. You can edit
area_timings.csv in Excel and run this file again (or just run the app).
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


from logic import MONTHLY_TEMP, duration_minutes, to_minutes

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# (area, light off, light on) - 24 hour clock, sample timings
TIMINGS = [
    ("Ghanta Ghar (Clock Tower)",          "10:30", "12:30"),
    ("Military Road",                      "10:00", "11:30"),
    ("Shikarpur Road",                     "13:00", "15:00"),
    ("Frere Road",                         "11:00", "12:30"),
    ("Minara Road",                        "14:00", "16:00"),
    ("Station Road",                       "09:30", "11:00"),
    ("Bunder Road",                        "15:00", "17:00"),
    ("Workshop Road",                      "12:00", "14:00"),
    ("Queens Road",                        "16:00", "17:30"),
    ("Shahi Bazaar",                       "10:30", "12:00"),
    ("Sarafa Bazaar",                      "11:30", "13:00"),
    ("Victoria Fruit Market",              "06:00", "07:30"),
    ("New Pind",                           "14:00", "16:00"),
    ("Old Sukkur",                         "13:30", "15:30"),
    ("Barrage Colony",                     "08:00", "10:00"),
    ("Labour Colony",                      "15:30", "18:00"),
    ("WAPDA Colony",                       "07:00", "08:00"),
    ("Nusrat Colony",                      "12:30", "14:30"),
    ("Railway Colony",                     "09:00", "11:00"),
    ("Regent Colony",                      "16:30", "18:30"),
    ("Shamsabad",                          "10:00", "12:30"),
    ("Marwari Mohalla",                    "14:30", "16:00"),
    ("Gharibabad",                         "11:00", "13:30"),
    ("Nawa Goth",                          "20:00", "22:30"),
    ("Pir Murad Shah Colony",              "13:00", "16:00"),
    ("Shah Latif Town",                    "08:30", "10:00"),
    ("Makki Shah",                         "15:00", "16:30"),
    ("Police Lines",                       "02:00", "04:00"),
    ("Sukkur Cooperative Housing Society", "12:00", "13:30"),
    ("Sukkur New City",                    "17:30", "19:00"),
    ("Cantonment Area",                    "07:30", "08:30"),
    ("SITE Area",                          "14:00", "17:00"),
]

HISTORY_DAYS = 365
HISTORY_END = date(2026, 11, 13)       # last day of the sample history
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def make_timings():
    df = pd.DataFrame(TIMINGS, columns=["Area", "Light Off Time", "Light On Time"])
    # safety check: every outage must finish on the same day
    for _, row in df.iterrows():
        assert to_minutes(row["Light Off Time"]) < to_minutes(row["Light On Time"]), row["Area"]
    df["Duration (minutes)"] = [
        duration_minutes(a, b) for a, b in zip(df["Light Off Time"], df["Light On Time"])
    ]
    df.to_csv(DATA_DIR / "area_timings.csv", index=False)
    return df


def make_history(timings):
    rng = np.random.default_rng(42)
    start = HISTORY_END - timedelta(days=HISTORY_DAYS - 1)
    days = [start + timedelta(days=i) for i in range(HISTORY_DAYS)]

    rows = []
    for _, area in timings.iterrows():
        # Each area has its own "load level": heavily loaded areas get load shedding more often.
        load_level = rng.uniform(0.55, 0.95)
        for day in days:
            temperature = round(MONTHLY_TEMP[day.month] + rng.normal(0, 2.0), 1)
            weekday = day.weekday()

            # Simple rule used for the SAMPLE data:
            #   hotter day -> more demand -> load shedding is more likely
            #   Friday and Sunday -> lower demand -> less likely
            score = load_level + 0.03 * (temperature - 28)
            if weekday == 6:      # Sunday
                score -= 0.35
            elif weekday == 4:    # Friday
                score -= 0.15

            happened = (score + rng.normal(0, 0.12)) > 0.5      # small random noise
            rows.append({
                "Date": day.isoformat(),
                "Area": area["Area"],
                "Temperature": temperature,
                "Day": DAY_NAMES[weekday],
                "Light Off Time": area["Light Off Time"] if happened else "",
                "Light On Time": area["Light On Time"] if happened else "",
                "Duration (minutes)": area["Duration (minutes)"] if happened else 0,
                "Load Shedding": "Yes" if happened else "No",
            })

    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "history.csv", index=False)
    return df


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    timings_df = make_timings()
    history_df = make_history(timings_df)
    print(f"area_timings.csv : {len(timings_df)} areas")
    print(f"history.csv      : {len(history_df)} rows "
          f"({HISTORY_DAYS} days x {len(timings_df)} areas)")
    print(history_df["Load Shedding"].value_counts())
